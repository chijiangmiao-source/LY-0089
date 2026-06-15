from django.db import models


class CrossVenueTransfer(models.Model):
    APPROVAL_STATUS_CHOICES = [
        ('pending', '待审批'),
        ('approved', '已批准'),
        ('rejected', '已拒绝'),
        ('cancelled', '已取消'),
    ]

    APPROVAL_STATUS_DISPLAY = {
        'pending': '待审批',
        'approved': '已批准',
        'rejected': '已拒绝',
        'cancelled': '已取消',
    }

    TRANSPORT_STATUS_CHOICES = [
        ('not_started', '未发货'),
        ('in_transit', '运输中'),
        ('arrived', '已到达'),
        ('confirmed', '已确认收货'),
    ]

    TRANSPORT_STATUS_DISPLAY = {
        'not_started': '未发货',
        'in_transit': '运输中',
        'arrived': '已到达',
        'confirmed': '已确认收货',
    }

    PRIORITY_CHOICES = [
        ('normal', '普通'),
        ('urgent', '紧急'),
    ]

    PRIORITY_DISPLAY = {
        'normal': '普通',
        'urgent': '紧急',
    }

    transfer_no = models.CharField(max_length=50, unique=True, verbose_name='跨场地调拨单号')
    from_venue = models.ForeignKey('venues.Venue', on_delete=models.PROTECT, related_name='outgoing_cross_transfers', verbose_name='申请场地')
    to_venue = models.ForeignKey('venues.Venue', on_delete=models.PROTECT, related_name='incoming_cross_transfers', verbose_name='目标场地')
    from_station = models.ForeignKey('stations.ServiceStation', on_delete=models.PROTECT, related_name='outgoing_cross_transfers', null=True, blank=True, verbose_name='源服务点')
    to_station = models.ForeignKey('stations.ServiceStation', on_delete=models.PROTECT, related_name='incoming_cross_transfers', null=True, blank=True, verbose_name='目标服务点')
    cart = models.ForeignKey('carts.Cart', on_delete=models.PROTECT, related_name='cross_venue_transfers', verbose_name='推车')
    cart_type = models.CharField(max_length=20, verbose_name='车型')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal', verbose_name='优先级')
    quantity = models.IntegerField(default=1, verbose_name='数量')
    reason = models.TextField(null=True, blank=True, verbose_name='调拨原因')
    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS_CHOICES, default='pending', verbose_name='审批状态')
    transport_status = models.CharField(max_length=20, choices=TRANSPORT_STATUS_CHOICES, default='not_started', verbose_name='运输状态')
    applicant = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='applied_cross_transfers', verbose_name='申请人')
    approver = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_cross_transfers', verbose_name='审批人')
    approver_comment = models.TextField(null=True, blank=True, verbose_name='审批意见')
    approval_at = models.DateTimeField(null=True, blank=True, verbose_name='审批时间')
    transporter = models.CharField(max_length=100, null=True, blank=True, verbose_name='运输方/司机')
    transport_tracking_no = models.CharField(max_length=100, null=True, blank=True, verbose_name='运输跟踪号')
    shipped_at = models.DateTimeField(null=True, blank=True, verbose_name='发货时间')
    arrived_at = models.DateTimeField(null=True, blank=True, verbose_name='到达时间')
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name='确认收货时间')
    confirmer = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='confirmed_cross_transfers', verbose_name='确认收货操作人')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'cross_venue_transfers'
        verbose_name = '跨场地调拨单'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.transfer_no

    @property
    def approval_status_display(self):
        return self.APPROVAL_STATUS_DISPLAY.get(self.approval_status, self.approval_status)

    @property
    def transport_status_display(self):
        return self.TRANSPORT_STATUS_DISPLAY.get(self.transport_status, self.transport_status)

    @property
    def priority_display(self):
        return self.PRIORITY_DISPLAY.get(self.priority, self.priority)
