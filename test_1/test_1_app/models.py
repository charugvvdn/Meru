from django.db import models


class controller(models.Model):
    cid = models.AutoField(primary_key=True)
    mac_address = models.CharField(max_length=256)
    user_id = models.IntegerField()
    ip_address = models.CharField(max_length=256)
    hostname = models.CharField(max_length=256)
    uptime = models.CharField(max_length=256)
    location = models.CharField(max_length=256)
    contact = models.CharField(max_length=256)
    operation_state = models.CharField(max_length=256)
    controller_model = models.CharField(max_length=256)
    software_version = models.CharField(max_length=256)
    country_settings = models.CharField(max_length=256)
    updated_on = models.IntegerField()
    updated_by = models.IntegerField()


class command(models.Model):
    command_id = models.AutoField(primary_key=True)
    controller_mac_address = models.CharField(max_length=256)
    flag = models.IntegerField(default=0)
    timestamp = models.IntegerField()


class alarm(models.Model):
    alarm_id = models.BigIntegerField(primary_key=True)
    controller_mac_address = models.CharField(max_length=256)
    alarm_type = models.CharField(max_length=256)
    severity = models.CharField(max_length=256)
    timestamp = models.CharField(max_length=256)
    content = models.CharField(max_length=256)
    cid = models.BigIntegerField()
    updated_on = models.IntegerField()
    is_read = models.IntegerField()
    sent_status = models.IntegerField(default=0)


class dashboard_info(models.Model):
    id = models.AutoField(primary_key=True)
    controller_mac = models.CharField(max_length=32)
    client_info = models.CharField(max_length=32)
    ap_info = models.CharField(max_length=32)
    alarm_info = models.CharField(max_length=32)
    ap_up = models.CharField(max_length=32)
    ap_down = models.CharField(max_length=32)
    client_up = models.CharField(max_length=32)
    client_down = models.CharField(max_length=32)
    updated_on = models.CharField(max_length=32, blank=True)


class ssid(models.Model):
    ssid = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256)
    enabled = models.IntegerField()
    visible = models.IntegerField()
    secured = models.CharField(max_length=256)
    action = models.CharField(max_length=256)
    dataplane_mode = models.CharField(max_length=256)
    security_profile_id = models.IntegerField()


class security_profile(models.Model):
    security_profile_id = models.AutoField(primary_key=True)
    profile_name = models.CharField(max_length=256)
    l2_mode = models.CharField(max_length=256)
    enc_mode = models.CharField(max_length=256)
    passphrase = models.CharField(max_length=256)
    radius_server_id = models.IntegerField()


class ssid_in_command(models.Model):
    id = models.AutoField(primary_key=True)
    command_id = models.IntegerField()
    ssid = models.IntegerField()


