from tortoise import Model, fields


class Tag(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)


class Device(Model):
    uuid = fields.CharField(max_length=255, pk=True)
    name = fields.CharField(max_length=255, null=True)
    fw_file = fields.CharField(max_length=255, default="latest")
    fw_version = fields.CharField(max_length=255, null=True)
    last_state = fields.CharField(max_length=255, null=True)
    last_log = fields.TextField(null=True)
    last_seen = fields.BigIntField(null=True)
    last_ip = fields.CharField(max_length=15, null=True)
    last_ipv6 = fields.CharField(max_length=40, null=True)
    tags = fields.ManyToManyField(
        "models.Tag", related_name="devices", through="device_tags"
    )
