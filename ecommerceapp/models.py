from django.db import models

class Product(models.Model):
    product_id = models.AutoField
    product_name = models.CharField(max_length=50)
    category = models.CharField(max_length=50, default="")
    subcategory = models.CharField(max_length=50, default="")
    price = models.IntegerField(default=0)
    desc = models.CharField(max_length=300)
    pub_date = models.DateField()

    image = models.ImageField(upload_to='images/images', default="")

    def __str__(self):
        return self.product_name


class Contact(models.Model):
    msg_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    email = models.CharField(max_length=70, default="")
    phone = models.CharField(max_length=70, default="")
    desc = models.CharField(max_length=500, default="")


    def __str__(self):
        return self.name


class Orders(models.Model):
    order_id = models.AutoField(primary_key=True)
    items_json =  models.CharField(max_length=5000)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    name = models.CharField(max_length=90)
    email = models.CharField(max_length=90)
    address1 = models.CharField(max_length=200)
    address2 = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=100)
    oid=models.CharField(max_length=50,blank=True)
    amountpaid=models.CharField(max_length=500,blank=True,null=True)
    paymentstatus=models.CharField(max_length=20,blank=True)
    phone = models.CharField(max_length=100,default="")
    timestamp = models.DateTimeField(auto_now_add=True, null=True)
    def __str__(self):
        return self.name
    


class OrderUpdate(models.Model):
    update_id = models.AutoField(primary_key=True)
    order_id = models.IntegerField(default="")
    update_desc = models.CharField(max_length=5000)
    delivered=models.BooleanField(default=False)
    timestamp = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.update_desc[0:7] + "..."

class PaymentTransaction(models.Model):
    PAYMENT_METHODS = [
        ('esewa', 'eSewa'),
        ('khalti', 'Khalti'),
    ]
    
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    transaction_id = models.CharField(max_length=100, unique=True)
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    gateway_transaction_id = models.CharField(max_length=100, blank=True, null=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.payment_method.upper()} - {self.transaction_id}"

class EsewaPayment(models.Model):
    payment_transaction = models.OneToOneField(PaymentTransaction, on_delete=models.CASCADE)
    merchant_code = models.CharField(max_length=50)
    product_code = models.CharField(max_length=50)
    transaction_uuid = models.CharField(max_length=100, unique=True)
    signature = models.TextField()
    success_url = models.URLField()
    failure_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"eSewa - {self.transaction_uuid}"

class KhaltiPayment(models.Model):
    payment_transaction = models.OneToOneField(PaymentTransaction, on_delete=models.CASCADE)
    purchase_order_id = models.CharField(max_length=100)
    purchase_order_name = models.CharField(max_length=200)
    return_url = models.URLField()
    website_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Khalti - {self.purchase_order_id}"