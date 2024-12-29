# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.utils import timezone


class Customers(models.Model):
    customerid = models.AutoField(db_column='CustomerID', primary_key=True)  # Field name made lowercase.
    customername = models.CharField(db_column='CustomerName', max_length=100, db_collation='Turkish_CI_AS')  # Field name made lowercase.
    budget = models.DecimalField(db_column='Budget', max_digits=10, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    customertype = models.CharField(db_column='CustomerType', max_length=10, db_collation='Turkish_CI_AS', blank=True, null=True)  # Field name made lowercase.
    totalspent = models.DecimalField(db_column='TotalSpent', max_digits=10, decimal_places=2, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Customers'


class Logadmin(models.Model):
    logid = models.AutoField(db_column='LogID', primary_key=True)
    islemdurumu = models.BooleanField(db_column='IslemDurumu')
    islem = models.CharField(db_column='Islem', max_length=50, db_collation='Turkish_CI_AS')
    date = models.DateTimeField(db_column='Date', blank=True, null=True)
    degisen = models.TextField(db_column='Degisen', db_collation='Turkish_CI_AS')

    class Meta:
        managed = True
        db_table = 'LogAdmin'


class Logs(models.Model):
    logid = models.AutoField(db_column='LogID', primary_key=True)  # Field name made lowercase.
    customerid = models.ForeignKey(Customers, models.DO_NOTHING, db_column='CustomerID', blank=True, null=True)  # Field name made lowercase.
    orderid = models.ForeignKey('Orders', models.DO_NOTHING, db_column='OrderID', blank=True, null=True)  # Field name made lowercase.
    logdate = models.DateTimeField(db_column='LogDate', blank=True, null=True)  # Field name made lowercase.
    logtype = models.CharField(db_column='LogType', max_length=20, db_collation='Turkish_CI_AS', blank=True, null=True)  # Field name made lowercase.
    logdetails = models.TextField(db_column='LogDetails', db_collation='Turkish_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Logs'


class Orders(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Beklemede'),
        ('Approved', 'Onaylandı'),
        ('Rejected', 'Reddedildi'),
        ('Completed', 'Tamamlandı')
    )

    orderid = models.AutoField(db_column='OrderID', primary_key=True)
    customerid = models.ForeignKey(Customers, models.DO_NOTHING, db_column='CustomerID', blank=True, null=True)
    productid = models.ForeignKey('Products', models.DO_NOTHING, db_column='ProductID', blank=True, null=True)
    quantity = models.IntegerField(db_column='Quantity', blank=True, null=True)
    totalprice = models.DecimalField(db_column='TotalPrice', max_digits=10, decimal_places=2, blank=True, null=True)
    orderdate = models.DateTimeField(db_column='OrderDate', blank=True, null=True)
    orderstatus = models.CharField(
        db_column='OrderStatus',
        max_length=20,
        db_collation='Turkish_CI_AS',
        choices=STATUS_CHOICES,
        default='Pending',
        blank=True,
        null=True
    )
    def get_waiting_time(self):
        duration = timezone.now() - self.orderdate if self.orderdate else 0
        seconds = int(duration.total_seconds()) if duration else 0
        return f"{seconds} saniye"
    class Meta:
        managed = False
        db_table = 'Orders'


class Products(models.Model):
    productid = models.AutoField(db_column='ProductID', primary_key=True)  # Field name made lowercase.
    productname = models.CharField(db_column='ProductName', max_length=100, db_collation='Turkish_CI_AS')  # Field name made lowercase.
    stock = models.IntegerField(db_column='Stock')  # Field name made lowercase.
    price = models.DecimalField(db_column='Price', max_digits=10, decimal_places=2)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Products'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150, db_collation='Turkish_CI_AS')

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255, db_collation='Turkish_CI_AS')
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100, db_collation='Turkish_CI_AS')

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128, db_collation='Turkish_CI_AS')
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150, db_collation='Turkish_CI_AS')
    first_name = models.CharField(max_length=150, db_collation='Turkish_CI_AS')
    last_name = models.CharField(max_length=150, db_collation='Turkish_CI_AS')
    email = models.CharField(max_length=254, db_collation='Turkish_CI_AS')
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(db_collation='Turkish_CI_AS', blank=True, null=True)
    object_repr = models.CharField(max_length=200, db_collation='Turkish_CI_AS')
    action_flag = models.SmallIntegerField()
    change_message = models.TextField(db_collation='Turkish_CI_AS')
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100, db_collation='Turkish_CI_AS')
    model = models.CharField(max_length=100, db_collation='Turkish_CI_AS')

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255, db_collation='Turkish_CI_AS')
    name = models.CharField(max_length=255, db_collation='Turkish_CI_AS')
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40, db_collation='Turkish_CI_AS')
    session_data = models.TextField(db_collation='Turkish_CI_AS')
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class ProcessappLogentry(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.CharField(max_length=100, db_collation='Turkish_CI_AS')
    action = models.CharField(max_length=100, db_collation='Turkish_CI_AS')
    date = models.DateTimeField()
    ip = models.CharField(max_length=39, db_collation='Turkish_CI_AS')
    status = models.CharField(max_length=50, db_collation='Turkish_CI_AS')
    detail = models.TextField(db_collation='Turkish_CI_AS')

    class Meta:
        managed = False
        db_table = 'processApp_logentry'


class Sysdiagrams(models.Model):
    name = models.CharField(max_length=128, db_collation='Turkish_CI_AS')
    principal_id = models.IntegerField()
    diagram_id = models.AutoField(primary_key=True)
    version = models.IntegerField(blank=True, null=True)
    definition = models.BinaryField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sysdiagrams'
        unique_together = (('principal_id', 'name'),)

class EditModeSettings(models.Model):
    is_edit_mode = models.BooleanField(default=False)
    
    def _str_(self):
        return f"Edit Mode: {'Açık' if self.is_edit_mode else 'Kapalı'}"
    
class PendingOrder(models.Model):
    customerid = models.ForeignKey(Customers, on_delete=models.CASCADE)
    productid = models.ForeignKey(Products, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    totalprice = models.DecimalField(max_digits=10, decimal_places=2)
    requestdate = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Pending')  # Pending, Approved, Rejected
    priority_score = models.IntegerField(default=0)
    request_time = models.DateTimeField(auto_now_add=True)
    related_order = models.OneToOneField(
        'Orders', on_delete=models.SET_NULL, null=True, blank=True
    )

    def calculate_priority_score(self):  # self parametresi eklendi
        base_score = 15 if self.customerid.customertype == 'Premium' else 10
        waiting_time = (timezone.now() - self.request_time).total_seconds()
        waiting_score = int(waiting_time * 0.5)  # int'e çevrildi
        total_score = base_score + waiting_score
        
        return total_score

    def update_priority_score(self):
        self.priority_score = self.calculate_priority_score()
        self.save()

    def approve_order(self):
        # Siparişi Orders tablosuna kaydet
        order = Orders.objects.create(
            customerid=self.customerid,
            productid=self.productid,
            quantity=self.quantity,
            totalprice=self.totalprice,
            orderdate=timezone.now(),
            orderstatus='Approved'
        )
        
        # PendingOrder'ın durumunu güncelle
        self.status = 'Approved'
        self.save()
        
        return order

    def reject_order(self):
        self.status = 'Rejected'
        self.save()

    class Meta:
        db_table = 'pending_orders'
                             
