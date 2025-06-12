# Generated manually for data migration
from django.db import migrations


def move_api_keys_from_home(apps, schema_editor):
    """
    將 UserAPIKey 資料從 home app 移動到 profiles app
    """
    # 取得舊的 home.UserAPIKey 模型
    try:
        HomeUserAPIKey = apps.get_model('home', 'UserAPIKey')
        ProfilesUserAPIKey = apps.get_model('profiles', 'UserAPIKey')
        
        # 複製所有資料
        for old_key in HomeUserAPIKey.objects.all():
            ProfilesUserAPIKey.objects.create(
                id=old_key.id,
                prefix=old_key.prefix,
                hashed_key=old_key.hashed_key,
                user=old_key.user,
                name=old_key.name,
                expires_at=old_key.expires_at,
                last_used_at=old_key.last_used_at,
                is_active=old_key.is_active,
                created_at=old_key.created_at,
                updated_at=old_key.updated_at,
                created=old_key.created,
                revoked=old_key.revoked,
            )
    except LookupError:
        # 如果 home.UserAPIKey 不存在，跳過
        pass


def reverse_move_api_keys_to_home(apps, schema_editor):
    """
    回滾操作：將資料移回 home app
    """
    pass  # 實際上我們不會回滾這個操作


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0001_initial'),
        ('home', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            move_api_keys_from_home,
            reverse_move_api_keys_to_home,
        ),
    ] 