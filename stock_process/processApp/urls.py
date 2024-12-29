from django.urls import path
from . import views

app_name = 'processApp'

urlpatterns = [
    path('', views.mainpage, name='mainpage'), 
    path('login/', views.login, name='login'),
    path('login/adminpanel/', views.adminpanel, name='adminpanel'),
    path('login/userpanel/', views.userpanel, name='userpanel'),
    path('stock_update/<int:productid>/', views.stock_update, name='stock_update'),
    path('login/userpanel/mybasket', views.mybasket, name='mybasket'),
    path('update-cart/', views.update_cart, name='update_cart'),
    path('remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
    path('submit-request/', views.submit_request, name='submit_request'),
    path('complete-request/', views.complete_request, name='complete_request'),
    path('delete-request/', views.delete_request, name='delete_request'),
    path('toggle_edit_mode/', views.toggle_edit_mode, name='toggle_edit_mode'),
    path('alert.html/',views.alert, name='alert.html'),
    path('handle-pending-order/', views.handle_pending_order, name='handle_pending_order'),
    path('queue/<int:order_id>/', views.queue, name='queue'),
    path('get-queue-position/<int:order_id>/', views.get_queue_position, name='get_queue_position'),
    path('queue/approved/', views.orderapproved, name='orderapproved'),
    path('queue/rejected/', views.orderrejected, name='orderrejected'),
]