from django.db import migrations


DEFAULT_COMPAT = {
    "O-": {"O-"},
    "O+": {"O-", "O+"},
    "A-": {"O-", "A-"},
    "A+": {"O-", "O+", "A-", "A+"},
    "B-": {"O-", "B-"},
    "B+": {"O-", "O+", "B-", "B+"},
    "AB-": {"O-", "A-", "B-", "AB-"},
    "AB+": {"O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"},
}

ALL = ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"]


def seed(apps, schema_editor):
    Model = apps.get_model("core", "BloodGroupCompatibility")
    for recipient, donors in DEFAULT_COMPAT.items():
        for donor in ALL:
            Model.objects.update_or_create(
                donor_group=donor,
                recipient_group=recipient,
                defaults={"is_compatible": donor in donors},
            )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]


