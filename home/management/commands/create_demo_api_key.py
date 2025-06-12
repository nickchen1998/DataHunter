from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from home.models import UserAPIKey


class Command(BaseCommand):
    help = '為指定使用者建立示範 API Key'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='使用者名稱',
            required=True
        )
        parser.add_argument(
            '--name',
            type=str,
            help='API Key 名稱',
            default='測試 API Key'
        )
        parser.add_argument(
            '--days',
            type=int,
            help='多少天後過期（預設 30 天，0 表示永不過期）',
            default=30
        )

    def handle(self, *args, **options):
        username = options['username']
        name = options['name']
        days = options['days']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'找不到使用者: {username}')
            )
            return
        
        # 計算到期時間
        expires_at = None
        if days > 0:
            expires_at = timezone.now() + timedelta(days=days)
        
        # 建立 API Key
        api_key, key = UserAPIKey.objects.create_key(
            user=user,
            name=name,
            expires_at=expires_at
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ 成功建立 API Key')
        )
        self.stdout.write(f'📝 使用者: {user.username}')
        self.stdout.write(f'🏷️  名稱: {name}')
        self.stdout.write(f'🔑 API Key: {key}')
        if expires_at:
            self.stdout.write(f'⏰ 過期時間: {expires_at.strftime("%Y-%m-%d %H:%M:%S")}')
        else:
            self.stdout.write(f'⏰ 過期時間: 永不過期')
        
        self.stdout.write(
            self.style.WARNING('\n⚠️  請妥善保存此 API Key，它不會再次顯示！')
        ) 