from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp


class Command(BaseCommand):
    help = '設置 Google OAuth 應用程式'

    def add_arguments(self, parser):
        parser.add_argument('--client-id', type=str, help='Google OAuth Client ID')
        parser.add_argument('--client-secret', type=str, help='Google OAuth Client Secret')

    def handle(self, *args, **options):
        client_id = options.get('client_id')
        client_secret = options.get('client_secret')
        
        if not client_id or not client_secret:
            self.stdout.write(
                self.style.ERROR(
                    '請提供 Google OAuth Client ID 和 Client Secret:\n'
                    'python manage.py setup_google_oauth --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET'
                )
            )
            return

        # 獲取或創建 Site
        site, created = Site.objects.get_or_create(
            id=1,
            defaults={
                'domain': 'localhost:8000',
                'name': 'RAGPilot Local'
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'創建了新的 Site: {site.domain}')
            )

        # 創建或更新 Google Social App
        google_app, created = SocialApp.objects.get_or_create(
            provider='google',
            defaults={
                'name': 'Google',
                'client_id': client_id,
                'secret': client_secret,
            }
        )
        
        if not created:
            # 更新現有的應用程式
            google_app.client_id = client_id
            google_app.secret = client_secret
            google_app.save()
            self.stdout.write(
                self.style.SUCCESS('更新了現有的 Google OAuth 應用程式')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('創建了新的 Google OAuth 應用程式')
            )

        # 將應用程式與 Site 關聯
        google_app.sites.add(site)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Google OAuth 設置完成！\n'
                f'Client ID: {client_id}\n'
                f'Site: {site.domain}\n'
                f'請確保在 Google Cloud Console 中設置正確的重定向 URI：\n'
                f'http://{site.domain}/accounts/google/login/callback/'
            )
        ) 