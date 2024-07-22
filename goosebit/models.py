from tortoise import Model, fields


class Tag(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255)


class Device(Model):
    uuid = fields.CharField(max_length=255, primary_key=True)
    name = fields.CharField(max_length=255, null=True)
    fw_file = fields.CharField(max_length=255, default="latest")
    fw_version = fields.CharField(max_length=255, null=True)
    hw_model = fields.CharField(max_length=255, null=True, default="default")
    hw_revision = fields.CharField(max_length=255, null=True, default="default")
    feed = fields.CharField(max_length=255, default="default")
    flavor = fields.CharField(max_length=255, default="default")
    last_state = fields.CharField(max_length=255, null=True, default="unknown")
    progress = fields.IntField(null=True)
    last_log = fields.TextField(null=True)
    last_seen = fields.BigIntField(null=True)
    last_ip = fields.CharField(max_length=15, null=True)
    last_ipv6 = fields.CharField(max_length=40, null=True)
    tags = fields.ManyToManyField(
        "models.Tag", related_name="devices", through="device_tags"
    )


class Rollout(Model):
    id = fields.IntField(primary_key=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    name = fields.CharField(max_length=255, null=True)
    hw_model = fields.CharField(max_length=255, default="default")
    hw_revision = fields.CharField(max_length=255, default="default")
    feed = fields.CharField(max_length=255, default="default")
    flavor = fields.CharField(max_length=255, default="default")
    fw_file = fields.CharField(max_length=255)
    paused = fields.BooleanField(default=False)
    success_count = fields.IntField(default=0)
    failure_count = fields.IntField(default=0)
