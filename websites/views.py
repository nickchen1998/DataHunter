from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Terms, UserTermsAgreement


@login_required
@require_POST
def agree_to_terms(request):
    """處理使用者同意條款的 AJAX 請求"""
    try:
        latest_terms = Terms.get_latest()
        if not latest_terms:
            return JsonResponse({
                'success': False,
                'message': '目前沒有有效的條款'
            })

        # 獲取客戶端資訊
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # 建立同意記錄
        agreement, created = UserTermsAgreement.create_agreement(
            user=request.user,
            terms=latest_terms,
            ip_address=ip_address,
            user_agent=user_agent
        )

        if created:
            return JsonResponse({
                'success': True,
                'message': '條款同意已記錄'
            })
        else:
            return JsonResponse({
                'success': True,
                'message': '您已經同意過此條款'
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'處理失敗：{str(e)}'
        })


@login_required
def check_terms_status(request):
    """檢查使用者是否需要同意條款"""
    latest_terms = Terms.get_latest()
    if not latest_terms:
        return JsonResponse({
            'needs_agreement': False,
            'terms_content': None
        })

    needs_agreement = not UserTermsAgreement.has_agreed_to_latest(request.user)
    
    return JsonResponse({
        'needs_agreement': needs_agreement,
        'terms_content': latest_terms.content if needs_agreement else None,
        'terms_title': latest_terms.title if needs_agreement else None,
        'terms_version': latest_terms.version if needs_agreement else None
    })


def get_client_ip(request):
    """獲取客戶端 IP 地址"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
