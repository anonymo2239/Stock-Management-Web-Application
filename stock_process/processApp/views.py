from urllib import request
from django.db import models
from .models import Customers, Products, Orders, Logs, Logadmin, EditModeSettings, PendingOrder
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
import json
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from datetime import datetime
from django.utils.timezone import now
from django.contrib import messages

# urls loginler
def mainpage(request):
    return render(request, 'mainpage.html')

def login(request):
    return render(request, 'login.html')

def alert(request):
    return render(request, 'alert.html')


def orderapproved(request):
    return render(request, 'orderapproved.html')

def orderrejected(request):
    return render(request, 'orderrejected.html')

# userpanel
def userpanel(request):
    settings = EditModeSettings.objects.first()
    if settings and settings.is_edit_mode:
        return render(request, 'alert.html')
    if 'username' in request.POST:  # Login işlemi
        customerid = request.POST.get('username')
        password = request.POST.get('password')
        
        customer = Customers.objects.get(customerid=customerid)
        if password == '1234':
            request.session['customerid'] = customer.customerid
            request.session['customername'] = customer.customername
            # Her kullanıcı için benzersiz bir sepet anahtarı oluştur
            request.session[f'cart_{customer.customerid}'] = {}
            
            all_customers = Customers.objects.all().order_by(models.F('totalspent').desc(nulls_last=True))
            all_products = Products.objects.all()
            
            return render(request, 'userpanel.html', {
                'customername': customer.customername,
                'customerbudget': customer.budget,
                'all_customers': all_customers,
                'products': all_products
            })
        return render(request, 'login.html', {'error': 'Hatalı şifre!'})
    
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        action = request.POST.get('action')
        
        if action == 'add_cart':
            quantity = int(request.POST.get('quantity', 1))
            product = Products.objects.get(productid=product_id)
            customer = Customers.objects.get(customerid=request.session['customerid'])
            
            # Kullanıcıya özel sepet anahtarını kullan
            cart_key = f'cart_{customer.customerid}'
            cart = request.session.get(cart_key, {})
            
            # Her bir üründen maksimum 5 adet kontrolü
            if quantity > 5:
                context = {
                    'customername': customer.customername,
                    'customerbudget': customer.budget,
                    'all_customers': Customers.objects.all().order_by(models.F('totalspent').desc(nulls_last=True)),
                    'products': Products.objects.all(),
                    'cart_total': calculate_cart_total(request, cart),
                    'error': 'Bir üründen en fazla 5 adet eklenebilir!'
                }
                return render(request, 'userpanel.html', context)
            
            # Stok kontrolü
            if product.stock < quantity:
                context = {
                    'customername': customer.customername,
                    'customerbudget': customer.budget,
                    'all_customers': Customers.objects.all().order_by(models.F('totalspent').desc(nulls_last=True)),
                    'products': Products.objects.all(),
                    'cart_total': calculate_cart_total(request, cart),
                    'error': f'{product.productname} için yeterli stok yok! (Mevcut stok: {product.stock})'
                }
                return render(request, 'userpanel.html', context)
            
            # Sepete ekleme işlemi
            cart[str(product_id)] = {
                'name': product.productname,
                'price': float(product.price),
                'quantity': quantity,
                'total': float(product.price) * quantity
            }
            
            request.session[cart_key] = cart
            request.session.modified = True

            context = {
                'customername': customer.customername,
                'customerbudget': customer.budget,
                'all_customers': Customers.objects.all().order_by(models.F('totalspent').desc(nulls_last=True)),
                'products': Products.objects.all(),
                'cart_total': calculate_cart_total(request, cart),
                'success': f'{product.productname} sepete eklendi!'
            }
            return render(request, 'userpanel.html', context)
    
    customer = Customers.objects.get(customerid=request.session['customerid'])
    cart_key = f'cart_{customer.customerid}'
    context = {
        'customername': customer.customername,
        'customerbudget': customer.budget,
        'all_customers': Customers.objects.all().order_by(models.F('totalspent').desc(nulls_last=True)),
        'products': Products.objects.all(),
        'cart_total': calculate_cart_total(request, request.session.get(cart_key, {}))
    }
    return render(request, 'userpanel.html', context)

def siparis_numarasi_olustur():
    settings = EditModeSettings.objects.first()
    if settings and settings.is_edit_mode:
        return render(request, 'alert.html')
    son_siparis = Orders.objects.aggregate(max('orderid'))['orderid__max']
    if son_siparis:
        return son_siparis + 1
    return 1000  # Başlangıç sipariş numarası

def calculate_cart_total(request, cart):
    settings = EditModeSettings.objects.first()
    if settings and settings.is_edit_mode:
        return render(request, 'alert.html')
    total = 0
    for item in cart.values():
        total += item['total']
    return total


# adminpanel
request_counter = 0
log_counter = 0
all_logs = {}
all_requests = {}

def adminpanel(request):
    # Veritabanından gerekli tüm verileri çek
    urunler = Products.objects.all().order_by('productid')
    logs = Logs.objects.all().order_by('-logdate')  # Logs tablosu
    log_admins = Logadmin.objects.all().order_by('-date')  # Logadmin tablosu
    pending_orders = PendingOrder.objects.all()
    selected_urun = None

    # Bekleyen siparişlerin öncelik skorlarını güncelle
    for order in pending_orders:
        order.update_priority_score()
    
    # Güncel skorlara göre siparişleri sırala
    pending_orders = pending_orders.order_by('-priority_score')
    

    if request.method == 'POST':
        # Sipariş onaylama/reddetme işlemleri
        if 'order_action' in request.POST:
            order_id = request.POST.get('order_id')
            action = request.POST.get('order_action')
            
            try:
                pending_order = PendingOrder.objects.get(id=order_id)
                
                if action == 'approve':
                    # Stok kontrolü
                    if pending_order.productid.stock >= pending_order.quantity:
                        try:
                            # Orders tablosuna kaydet
                            Orders.objects.create(
                                customerid=pending_order.customerid,
                                productid=pending_order.productid,
                                quantity=pending_order.quantity,
                                totalprice=pending_order.totalprice,
                                orderdate=now(),
                                orderstatus='Approved'
                            )
                            
                            # Stoku güncelle
                            product = pending_order.productid
                            product.stock -= pending_order.quantity
                            product.save()
                            
                            # PendingOrder'ı sil
                            pending_order.delete()
                            
                            # Logadmin kaydı
                            Logadmin.objects.create(
                                islemdurumu=True,
                                islem='Sipariş Onaylama',
                                date=now(),
                                degisen=f"Sipariş ID: {order_id} onaylandı"
                            )
                            
                            messages.success(request, 'Sipariş başarıyla onaylandı.')
                            
                        except Exception as e:
                            messages.error(request, f'Sipariş onaylanırken bir hata oluştu: {str(e)}')
                            Logadmin.objects.create(
                                islemdurumu=False,
                                islem='Sipariş Onaylama Hatası',
                                date=now(),
                                degisen=f"Sipariş ID: {order_id} - Hata: {str(e)}"
                            )
                        
                    else:
                        messages.error(request, 'Yetersiz stok!')
                        Logadmin.objects.create(
                            islemdurumu=False,
                            islem='Sipariş Onaylama Hatası',
                            date=now(),
                            degisen=f"Sipariş ID: {order_id} - Yetersiz stok"
                        )
                
                elif action == 'reject':
                    try:
                        # PendingOrder'ı sil
                        pending_order.delete()
                        
                        Logadmin.objects.create(
                            islemdurumu=True,
                            islem='Sipariş Reddetme',
                            date=now(),
                            degisen=f"Sipariş ID: {order_id} reddedildi"
                        )
                        
                        messages.info(request, 'Sipariş reddedildi.')
                        
                    except Exception as e:
                        messages.error(request, f'Sipariş reddedilirken bir hata oluştu: {str(e)}')
                        Logadmin.objects.create(
                            islemdurumu=False,
                            islem='Sipariş Reddetme Hatası',
                            date=now(),
                            degisen=f"Sipariş ID: {order_id} - Hata: {str(e)}"
                        )
            
            
            except PendingOrder.DoesNotExist:
                 pass
        # Ürün güncelleme işlemleri
        elif 'productid' in request.POST:
            try:
                selected_urun = get_object_or_404(Products, productid=request.POST['productid'])
                old_values = {
                    'name': selected_urun.productname,
                    'stock': selected_urun.stock,
                    'price': selected_urun.price
                }
                
                # Yeni değerleri al ve doğrula
                new_name = request.POST.get('productName', '').strip()
                new_stock = request.POST.get('stock', '')
                new_price = request.POST.get('price', '')
                
                if new_name:
                    selected_urun.productname = new_name
                
                if new_stock.isdigit():
                    selected_urun.stock = int(new_stock)
                
                try:
                    if new_price:
                        selected_urun.price = Decimal(new_price)
                except:
                    messages.error(request, 'Geçersiz fiyat formatı!')
                    return redirect('adminpanel')
                
                selected_urun.save()
                
                changes = []
                if old_values['name'] != selected_urun.productname:
                    changes.append(f"İsim: {old_values['name']} -> {selected_urun.productname}")
                if old_values['stock'] != selected_urun.stock:
                    changes.append(f"Stok: {old_values['stock']} -> {selected_urun.stock}")
                if old_values['price'] != selected_urun.price:
                    changes.append(f"Fiyat: {old_values['price']} -> {selected_urun.price}")
                
                change_text = ', '.join(changes)
                
                # Logadmin kaydı
                print("Logadmin kaydı oluşturuluyor...")
                Logadmin.objects.create(
                    islemdurumu=True,
                    islem='Ürün Güncelleme',
                    date=now(),
                    degisen=f"Ürün ID: {selected_urun.productid} - Değişiklikler: {change_text}"
                )
                print("Logadmin kaydı başarıyla oluşturuldu.")
                
                messages.success(request, 'Ürün başarıyla güncellendi.')
                
            except Exception as e:
                messages.error(request, f'Ürün güncellenirken bir hata oluştu: {str(e)}')
                try:
                    Logadmin.objects.create(
                        islemdurumu=False,
                        islem='Ürün Güncelleme Hatası',
                        date=now(),
                        degisen=f"Ürün ID: {request.POST['productid']} - Hata: {str(e)}"
                    )
                except Exception as log_error:
                    print(f"Logadmin hata kaydı oluşturulurken hata: {log_error}")
    context = {
        'urunler': urunler,
        'selected_urun': selected_urun,
        'logs': logs,  # Logs modeli ekleniyor
        'log_admins': log_admins,  # Logadmin modeli ekleniyor
        'pending_orders': pending_orders,
        'customer_requests': all_requests,
    }

    return render(request, 'adminpanel.html', context)

def submit_request(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        
        # Talebi sözlüğe ekle
        request_id = len(all_requests) + 1  # Sadece sözlük için bir ID oluşturuyoruz
        all_requests[request_id] = {
            'product_id': data['product_id'],
            'product_name': data['product_name'],
            'amount': data['amount'],
            'customer_name': data['customer_name'],
            'id': request_id
        }

        # Müşteri log kaydı ekle (Logs tablosuna)
        try:
            Logs.objects.create(
                customerid=data.get('customer_id'),
                orderid=None,
                logdate=now(),
                logtype='Information',
                logdetails=f"{data['product_name']} ürününden {data['amount']} adet talep edildi"
            )
        except Exception as e:
            print(f"Log ekleme hatası: {str(e)}")
            return JsonResponse({'status': 'error', 'message': 'Log ekleme hatası'}, status=500)

        return JsonResponse({
            'status': 'success',
            'request_id': request_id
        })
    
    return JsonResponse({'status': 'error'}, status=400)

def delete_request(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        request_id = int(data.get('request_id'))
        
        if request_id in all_requests:
            # Admin log kaydı ekle
            add_log(
                user=request.user.username,
                user_type='admin',
                action='Talep Silme',
                ip=request.META.get('REMOTE_ADDR'),
                status='Başarılı',
                detail=f"Talep ID: {request_id} silindi"
            )
            
            del all_requests[request_id]
            return JsonResponse({
                'status': 'success',
                'message': 'Talep başarıyla silindi'
            })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Talep silinemedi'
    }, status=400)

def complete_request(request):
    if request.method == 'POST':
        try:
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse(
                    {'status': 'error', 'message': 'Geçersiz JSON verisi'},
                    status=400
                )
            
            order_id = int(data.get('request_id'))
            
            # Global all_requests'i kullan
            global all_requests
            
            if order_id not in all_requests:
                return JsonResponse(
                    {'status': 'error', 'message': 'Talep bulunamadı'},
                    status=400
                )

            request_info = all_requests[order_id]

            add_log(
                user=request.user.username,
                user_type='admin',
                action='Talep Tamamlama',
                ip=request.META.get('REMOTE_ADDR'),
                status='Başarılı',
                detail=f"{request_info['customer_name']}'in {request_info['product_name']} talebi tamamlandı"
            )

            log_admin = Logadmin(
                islemdurumu=True,
                islem='Talep Tamamlama',
                date=timezone.now(),
                degisen=f"Talep ID: {order_id} - {request_info['customer_name']}'in {request_info['product_name']} talebi tamamlandı"
            )
            log_admin.save()

            # Talebi sözlükten kaldır
            del all_requests[order_id]

            return JsonResponse({
                'status': 'success',
                'message': 'Talep başarıyla tamamlandı'
            })

        except Exception as e:
            print("Hata:", str(e))
            return JsonResponse({
                'status': 'error',
                'message': 'Bir sistem hatası oluştu'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Geçersiz istek metodu'
    }, status=405)

@csrf_exempt  # CSRF kontrolünü devre dışı bırakmak gerekiyorsa kullanabilirsiniz
def stock_update(request, productid):
    if request.method == 'POST':
        try:
            # Ürün bilgilerini al ve eski değerleri sakla
            urun = get_object_or_404(Products, productid=productid)
            eski_stok = urun.stock
            eski_fiyat = urun.price
            eski_isim = urun.productname

            # Yeni değerleri al ve güncelle
            urun.productname = request.POST.get('productName', urun.productname)
            urun.stock = int(request.POST.get('stock', urun.stock))
            urun.price = float(request.POST.get('price', urun.price))
            urun.save()

            # Logadmin tablosuna log kaydını ekle
            Logadmin.objects.create(
                islemdurumu=True,  # Doğru alan adı
                islem="Güncelleme",  # İşlem türü
                date=now(),  # İşlem tarihi
                degisen=f"Ürün ID: {urun.productid}, "
                        f"Adı: {eski_isim} -> {urun.productname}, "
                        f"Stok: {eski_stok} -> {urun.stock}, "
                        f"Fiyat: {eski_fiyat:.2f} -> {urun.price:.2f}"
            )

            # Başarılı yanıt
            return JsonResponse({
                'status': 'success',
                'message': 'Ürün başarıyla güncellendi ve log kaydedildi!',
                'updated_product': {
                    'productid': urun.productid,
                    'productname': urun.productname,
                    'stock': urun.stock,
                    'price': urun.price,
                }
            })

        except Exception as e:
            # Hata durumunda log kaydını ekle
            Logadmin.objects.create(
                islemdurumu=False,  # Doğru alan adı
                islem="Güncelleme",  # İşlem türü
                date=now(),  # İşlem tarihi
                degisen=f"Ürün ID: {productid} - Güncelleme sırasında hata oluştu"
            )

            # Hata yanıtı
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    else:
        # GET veya diğer yöntemler için yanıt
        return JsonResponse({'status': 'error', 'message': 'Bu endpoint yalnızca POST isteği kabul eder.'}, status=405)

def add_log(user, user_type, action, ip, status, detail):
    global log_counter
    log_counter += 1
    all_logs[log_counter] = {
        'id': log_counter,
        'user': user,
        'user_type': user_type,
        'action': action,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'ip': ip,
        'status': status,
        'detail': detail
    }


def toggle_edit_mode(request):
    # İlk kaydı al veya oluştur
    settings, created = EditModeSettings.objects.get_or_create(id=1)
    
    # Değeri tersine çevir
    settings.is_edit_mode = not settings.is_edit_mode
    settings.save()

    # Edit mode durumunu session'a kaydet
    request.session['edit_mode'] = settings.is_edit_mode

    return redirect(request.META.get('HTTP_REFERER', '/adminpanel/'))

@csrf_exempt  # Eğer sorun yaşarsanız, bu satırı kaldırmayın.
def handle_pending_order(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        order_id = data.get('order_id')
        action = data.get('action')

        if not order_id or not action:
            return JsonResponse({'success': False, 'error': 'Eksik bilgi: Order ID veya Action tanımlı değil.'})

        # Siparişi bul ve işlemleri yap.
        try:
            pending_order = PendingOrder.objects.get(id=order_id)
            if action == 'approve':
                pending_order.status = 'Approved'
                pending_order.save()
                return JsonResponse({'success': True, 'message': 'Sipariş onaylandı!'})
            elif action == 'reject':
                pending_order.status = 'Rejected'
                pending_order.save()
                return JsonResponse({'success': True, 'message': 'Sipariş reddedildi!'})
            else:
                return JsonResponse({'success': False, 'error': 'Geçersiz işlem.'})
        except PendingOrder.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Sipariş bulunamadı.'})
    else:
        return JsonResponse({'success': False, 'error': 'Geçersiz istek yöntemi.'})








# mybasket
def mybasket(request):
    settings = EditModeSettings.objects.first()
    if settings and settings.is_edit_mode:
        return render(request, 'alert.html')
    if 'customerid' not in request.session:
        return redirect('processApp:login')

    musteri = Customers.objects.get(customerid=request.session['customerid'])
    sepet_key = f'cart_{musteri.customerid}'
    sepet = request.session.get(sepet_key, {})
    
    toplam_tutar = Decimal('0')
    try:
        for item in sepet.values():
            item_total = Decimal(str(item['total']))
            toplam_tutar += item_total
    except Exception as e:
        print(f"Toplam tutar hesaplama hatası: {str(e)}")
        return render(request, 'mybasket.html', {'error': 'Sepet tutarı hesaplanırken hata oluştu!'})

    if request.method == 'POST' and 'place_order' in request.POST:
        if not sepet:
            Logs.objects.create(
                customerid=musteri,
                logdate=timezone.now(),
                logtype='Warning',
                logdetails='Boş sepet ile sipariş verilmeye çalışıldı'
            )
            return render(request, 'mybasket.html', {'error': 'Sepetiniz boş!'})

        try:
            print("Toplam tutar (tip):", type(toplam_tutar))
            print("Toplam tutar (değer):", toplam_tutar)

            if musteri.customertype == 'Standard' and toplam_tutar > Decimal('1000'):
                Logs.objects.create(
                    customerid=musteri,
                    logdate=timezone.now(),
                    logtype='Warning',
                    logdetails=f'Standard müşteri {toplam_tutar} TL tutarında sipariş vermeye çalıştı'
                )
                return render(request, 'mybasket.html', {
                    'cart': sepet,
                    'total_price': toplam_tutar,
                    'error': 'Standard müşteriler 1000 TL üzeri sipariş veremez!'
                })

            for urun_id, urun in sepet.items():
                product = Products.objects.get(productid=urun_id)
                miktar = int(urun['quantity'])
                
                if miktar <= 0 or miktar > 5:
                    Logs.objects.create(
                        customerid=musteri,
                        logdate=timezone.now(),
                        logtype='Warning',
                        logdetails=f'Geçersiz miktar ({miktar}) ile sipariş verilmeye çalışıldı'
                    )
                    return render(request, 'mybasket.html', {
                        'cart': sepet,
                        'total_price': toplam_tutar,
                        'error': 'Sipariş miktarı 1 ile 5 arasında olmalıdır.'
                    })

                if product.stock < miktar:
                    Logs.objects.create(
                        customerid=musteri,
                        logdate=timezone.now(),
                        logtype='Warning',
                        logdetails=f'{product.productname} için yetersiz stok. İstenen: {miktar}, Mevcut: {product.stock}'
                    )
                    return render(request, 'mybasket.html', {
                        'cart': sepet,
                        'total_price': toplam_tutar,
                        'error': f'{product.productname} için yeterli stok yok!'
                    })

            if musteri.budget is None:
                return render(request, 'mybasket.html', {
                    'cart': sepet,
                    'total_price': toplam_tutar,
                    'error': 'Müşteri bütçesi tanımlanmamış!'
                })

            musteri_butce = Decimal(str(musteri.budget))
            yeni_butce = musteri_butce - toplam_tutar
            
            if yeni_butce < 500 or yeni_butce > 3000:
                Logs.objects.create(
                    customerid=musteri,
                    logdate=timezone.now(),
                    logtype='Warning',
                    logdetails=f'Bütçe sınırı aşıldı. Yeni bütçe: {yeni_butce} TL'
                )
                return render(request, 'mybasket.html', {
                    'cart': sepet,
                    'total_price': toplam_tutar,
                    'error': f'İşlem sonrası bütçeniz ({yeni_butce} TL) izin verilen aralıkta (500-3000 TL) olmayacak!'
                })

            first_pending_order = None
            
            for urun_id, urun in sepet.items():
                product = Products.objects.get(productid=urun_id)
                miktar = int(urun['quantity'])
                urun_toplam = Decimal(str(urun['total']))

                priority_score = calculate_priority_score(musteri, urun_toplam)

                pending_order = PendingOrder.objects.create(
                    customerid=musteri,
                    productid=product,
                    quantity=miktar,
                    totalprice=urun_toplam,
                    priority_score=priority_score
                )
                
                if first_pending_order is None:
                    first_pending_order = pending_order

                musteri.budget = musteri_butce - urun_toplam
                musteri.save()

                # Log kaydını orderid olmadan oluştur
                Logs.objects.create(
                    customerid=musteri,
                    logdate=timezone.now(),
                    logtype='Information',
                    logdetails=f'Yeni sipariş oluşturuldu: {product.productname} x{miktar} = {urun_toplam} TL'
                )

            request.session[sepet_key] = {}
            request.session.modified = True

            return redirect('processApp:queue', order_id=first_pending_order.id)

        except Exception as e:
            Logs.objects.create(
                customerid=musteri,
                logdate=timezone.now(),
                logtype='Error',
                logdetails=f'Sipariş oluşturma hatası: {str(e)}'
            )
            print(f"Hata: {str(e)}")
            return render(request, 'mybasket.html', {
                'cart': sepet,
                'total_price': toplam_tutar,
                'error': 'Sipariş işlemi sırasında bir hata oluştu!'
            })

    return render(request, 'mybasket.html', {
        'cart': sepet,
        'total_price': toplam_tutar
    })

def calculate_priority_score(musteri, siparis_tutari):
    try:
        # Temel puan
        if musteri.customertype == 'Premium':
            base_score = Decimal('100')
        else:
            base_score = Decimal('50')

        # Toplam harcama puanı
        if musteri.totalspent:
            # totalspent değerini Decimal'e çeviriyoruz
            totalspent = Decimal(str(musteri.totalspent))
            spending_score = (totalspent / Decimal('1000')) * Decimal('10')
        else:
            spending_score = Decimal('0')

        # Sipariş tutarı puanını Decimal'e çeviriyoruz
        siparis_tutari = Decimal(str(siparis_tutari))
        order_score = (siparis_tutari / Decimal('100')) * Decimal('5')

        # Toplam puanı hesapla
        total_score = base_score + spending_score + order_score

        return round(float(total_score), 2)  # float'a çevirip yuvarlıyoruz

    except Exception as e:
        print(f"Öncelik skoru hesaplama hatası: {str(e)}")
        return 0

def queue(request, order_id):
    if 'customerid' not in request.session:
        return redirect('processApp:login')

    try:
        musteri = Customers.objects.get(customerid=request.session['customerid'])
        siparis = PendingOrder.objects.get(id=order_id, customerid=musteri)
        
        tum_siparisler = PendingOrder.objects.all().order_by('-priority_score')
        sira = list(tum_siparisler).index(siparis) + 1
        
        return render(request, 'queue.html', {
            'order': siparis,
            'queue_position': sira
        })
    except (PendingOrder.DoesNotExist, Customers.DoesNotExist):
        return redirect('processApp:userpanel')

def get_queue_position(request, order_id):
    try:
        order = PendingOrder.objects.get(id=order_id)
        queue_position = PendingOrder.objects.filter(priority_score__gt=order.priority_score).count() + 1
        estimated_wait = (queue_position - 1) * 5
        total_orders = PendingOrder.objects.count()
        progress = ((total_orders - queue_position + 1) / total_orders) * 100 if total_orders > 0 else 0

        # Doğru alanları kontrol edin
        is_approved = hasattr(order, 'status') and order.status == 'Approved'
        is_rejected = hasattr(order, 'status') and order.status == 'Rejected'

        return JsonResponse({
            'position': queue_position,
            'estimated_wait': estimated_wait,
            'progress': progress,
            'is_approved': is_approved,
            'is_rejected': is_rejected
        })
    except PendingOrder.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Order not found'})


@csrf_exempt
def update_cart(request):
    settings = EditModeSettings.objects.first()
    if settings and settings.is_edit_mode:
        return render(request, 'alert.html')
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = str(data.get('product_id'))
            quantity = int(data.get('quantity'))
            
            customer = Customers.objects.get(customerid=request.session['customerid'])
            cart_key = f'cart_{customer.customerid}'
            cart = request.session.get(cart_key, {})
            
            # Quantity kontrolü
            if quantity <= 0:
                return JsonResponse({
                    'success': False, 
                    'error': 'Ürün miktarı 0\'dan büyük olmalıdır.'
                })
            
            # Toplam ürün kontrolü
            total_items = sum(item['quantity'] for item_id, item in cart.items() if item_id != product_id)
            if total_items + quantity > 5:
                return JsonResponse({
                    'success': False,
                    'error': 'Sepette en fazla 5 ürün olabilir!'
                })
            
            # Stok kontrolü
            product = Products.objects.get(productid=product_id)
            if product.stock < quantity:
                return JsonResponse({
                    'success': False,
                    'error': f'Yeterli stok yok! (Mevcut stok: {product.stock})'
                })
            
            if product_id in cart:
                price = cart[product_id]['price']
                cart[product_id]['quantity'] = quantity
                cart[product_id]['total'] = price * quantity
                
                request.session[cart_key] = cart
                request.session.modified = True
                
                return JsonResponse({
                    'success': True,
                    'message': 'Sepet başarıyla güncellendi'
                })
                
        except Products.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Ürün bulunamadı!'
            })
        except Exception as e:
            print(f"Hata: {str(e)}")
            return JsonResponse({
                'success': False, 
                'error': 'Bir hata oluştu: ' + str(e)
            })
            
    return JsonResponse({
        'success': False,
        'error': 'Geçersiz istek metodu'
    })

@csrf_exempt
def remove_from_cart(request):
    settings = EditModeSettings.objects.first()
    if settings and settings.is_edit_mode:
        return render(request, 'alert.html')
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = str(data.get('product_id'))
            
            customer = Customers.objects.get(customerid=request.session['customerid'])
            cart_key = f'cart_{customer.customerid}'
            cart = request.session.get(cart_key, {})
            
            if product_id in cart:
                del cart[product_id]
                
                request.session[cart_key] = cart
                request.session.modified = True
                
                return JsonResponse({'success': True})
        except Exception as e:
            print(f"Hata: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False})


############################################
