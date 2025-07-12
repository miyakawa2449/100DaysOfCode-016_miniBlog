"""
GA4 Analytics Manager
Google Analytics 4 統合と高度な追跡機能を提供
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import re
from models import SiteSetting

class GA4AnalyticsManager:
    """GA4分析管理クラス"""
    
    def __init__(self):
        self.measurement_id = SiteSetting.get_setting('google_analytics_id', '')
        self.gtm_id = SiteSetting.get_setting('google_tag_manager_id', '')
        self.enabled = SiteSetting.get_setting('google_analytics_enabled', 'false').lower() == 'true'
        self.track_admin = SiteSetting.get_setting('analytics_track_admin', 'false').lower() == 'true'
    
    def get_gtag_config(self) -> Dict[str, Any]:
        """gtag設定オブジェクトを生成"""
        config = {
            'page_title': 'document.title',
            'page_location': 'window.location.href',
            'custom_map': {}
        }
        
        # Enhanced Ecommerce設定
        if SiteSetting.get_setting('enhanced_ecommerce_enabled', 'false').lower() == 'true':
            config['custom_map']['custom_parameter_1'] = 'content_group1'
        
        # ユーザープロパティ設定
        if SiteSetting.get_setting('track_user_properties', 'false').lower() == 'true':
            config['user_properties'] = {
                'visitor_type': 'new_visitor'
            }
        
        return config
    
    def get_privacy_config(self) -> Dict[str, Any]:
        """プライバシー設定を生成"""
        analytics_storage = SiteSetting.get_setting('analytics_storage', 'denied')
        ad_storage = SiteSetting.get_setting('ad_storage', 'denied')
        
        return {
            'analytics_storage': analytics_storage,
            'ad_storage': ad_storage,
            'region': ['AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR', 'DE', 'GR', 'HU', 'IE', 'IT', 'LV', 'LT', 'LU', 'MT', 'NL', 'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE']  # EU諸国
        }
    
    def generate_base_tracking_code(self) -> str:
        """基本トラッキングコードを生成"""
        if not self.enabled or not self.measurement_id:
            return ""
        
        privacy_config = self.get_privacy_config()
        gtag_config = self.get_gtag_config()
        
        # GDPR対応のためのConsent Mode設定
        consent_code = f"""
<!-- Google Consent Mode -->
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){{dataLayer.push(arguments);}}

gtag('consent', 'default', {{
  'analytics_storage': '{privacy_config['analytics_storage']}',
  'ad_storage': '{privacy_config['ad_storage']}',
  'region': {json.dumps(privacy_config['region'])}
}});
</script>
"""
        
        # GA4基本トラッキングコード
        base_code = f"""
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={self.measurement_id}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  
  gtag('config', '{self.measurement_id}', {json.dumps(gtag_config, indent=2)});
</script>
"""
        
        return consent_code + base_code
    
    def generate_enhanced_tracking_code(self) -> str:
        """拡張トラッキング機能のJavaScriptコードを生成"""
        if not self.enabled:
            return ""
        
        code_parts = []
        
        # スクロール追跡
        if SiteSetting.get_setting('track_scroll_events', 'true').lower() == 'true':
            code_parts.append(self._get_scroll_tracking_code())
        
        # ファイルダウンロード追跡
        if SiteSetting.get_setting('track_file_downloads', 'true').lower() == 'true':
            code_parts.append(self._get_download_tracking_code())
        
        # 外部リンク追跡
        if SiteSetting.get_setting('track_external_links', 'true').lower() == 'true':
            code_parts.append(self._get_external_link_tracking_code())
        
        # ページエンゲージメント追跡
        if SiteSetting.get_setting('track_page_engagement', 'true').lower() == 'true':
            code_parts.append(self._get_page_engagement_tracking_code())
        
        # サイト内検索追跡
        if SiteSetting.get_setting('track_site_search', 'true').lower() == 'true':
            code_parts.append(self._get_site_search_tracking_code())
        
        if code_parts:
            return f"""
<script>
// Enhanced GA4 Tracking
document.addEventListener('DOMContentLoaded', function() {{
  {chr(10).join(code_parts)}
}});
</script>
"""
        return ""
    
    def _get_scroll_tracking_code(self) -> str:
        """スクロール追跡コード"""
        return """
  // スクロール追跡
  let scrollTimer;
  let scrolled = false;
  window.addEventListener('scroll', function() {
    if (!scrolled) {
      scrolled = true;
      gtag('event', 'scroll', {
        'event_category': 'engagement',
        'event_label': 'first_scroll'
      });
    }
    
    clearTimeout(scrollTimer);
    scrollTimer = setTimeout(function() {
      const scrollPercent = Math.round((window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100);
      if (scrollPercent >= 90) {
        gtag('event', 'scroll', {
          'event_category': 'engagement',
          'event_label': 'scroll_90_percent',
          'value': scrollPercent
        });
      }
    }, 1000);
  });
"""
    
    def _get_download_tracking_code(self) -> str:
        """ファイルダウンロード追跡コード"""
        return """
  // ファイルダウンロード追跡
  document.addEventListener('click', function(e) {
    const link = e.target.closest('a');
    if (link && link.href) {
      const fileExtensions = /\\.(pdf|doc|docx|xls|xlsx|ppt|pptx|zip|txt|csv)$/i;
      if (fileExtensions.test(link.href)) {
        gtag('event', 'file_download', {
          'event_category': 'engagement',
          'event_label': link.href,
          'value': 1
        });
      }
    }
  });
"""
    
    def _get_external_link_tracking_code(self) -> str:
        """外部リンク追跡コード"""
        return """
  // 外部リンク追跡
  document.addEventListener('click', function(e) {
    const link = e.target.closest('a');
    if (link && link.href && link.hostname !== window.location.hostname) {
      gtag('event', 'click', {
        'event_category': 'outbound',
        'event_label': link.href,
        'transport_type': 'beacon'
      });
    }
  });
"""
    
    def _get_page_engagement_tracking_code(self) -> str:
        """ページエンゲージメント追跡コード"""
        return """
  // ページエンゲージメント追跡
  let startTime = Date.now();
  let engaged = false;
  
  function trackEngagement() {
    if (!engaged) {
      engaged = true;
      gtag('event', 'page_view', {
        'event_category': 'engagement',
        'event_label': 'engaged_session',
        'engaged_session_event': 1
      });
    }
  }
  
  // 10秒滞在またはスクロールで engaged とみなす
  setTimeout(trackEngagement, 10000);
  
  window.addEventListener('beforeunload', function() {
    const timeOnPage = Math.round((Date.now() - startTime) / 1000);
    if (timeOnPage > 5) {
      gtag('event', 'timing_complete', {
        'name': 'page_read_time',
        'value': timeOnPage
      });
    }
  });
"""
    
    def _get_site_search_tracking_code(self) -> str:
        """サイト内検索追跡コード"""
        return """
  // サイト内検索追跡
  const searchForms = document.querySelectorAll('form[action*="search"], .search-form');
  searchForms.forEach(function(form) {
    form.addEventListener('submit', function(e) {
      const searchInput = form.querySelector('input[type="search"], input[name*="search"], input[name="q"]');
      if (searchInput && searchInput.value) {
        gtag('event', 'search', {
          'search_term': searchInput.value,
          'event_category': 'site_search'
        });
      }
    });
  });
"""
    
    def generate_cookie_consent_banner(self) -> str:
        """Cookie同意バナーのHTMLとJSを生成"""
        if not SiteSetting.get_setting('cookie_consent_enabled', 'true').lower() == 'true':
            return ""
        
        banner_text = SiteSetting.get_setting('consent_banner_text', 
            'このサイトではCookieを使用してサイトの利用状況を分析し、ユーザー体験を向上させています。')
        privacy_url = SiteSetting.get_setting('privacy_policy_url', '/privacy-policy')
        
        return f"""
<!-- Cookie Consent Banner -->
<div id="cookieConsentBanner" style="display: none; position: fixed; bottom: 0; left: 0; right: 0; background: #333; color: white; padding: 15px; z-index: 9999; text-align: center;">
  <div style="max-width: 1200px; margin: 0 auto;">
    <p style="margin: 0 0 10px 0; font-size: 14px;">{banner_text}</p>
    <div>
      <a href="{privacy_url}" target="_blank" style="color: #fff; text-decoration: underline; margin-right: 15px;">プライバシーポリシー</a>
      <button onclick="acceptCookies()" style="background: #007bff; color: white; border: none; padding: 8px 16px; margin: 0 5px; cursor: pointer; border-radius: 4px;">同意する</button>
      <button onclick="declineCookies()" style="background: #6c757d; color: white; border: none; padding: 8px 16px; margin: 0 5px; cursor: pointer; border-radius: 4px;">拒否する</button>
    </div>
  </div>
</div>

<script>
// Cookie同意管理
function checkCookieConsent() {{
  const consent = localStorage.getItem('cookieConsent');
  if (!consent) {{
    document.getElementById('cookieConsentBanner').style.display = 'block';
  }} else if (consent === 'accepted') {{
    updateConsentMode('granted', 'granted');
  }}
}}

function acceptCookies() {{
  localStorage.setItem('cookieConsent', 'accepted');
  document.getElementById('cookieConsentBanner').style.display = 'none';
  updateConsentMode('granted', 'granted');
  
  // Analytics re-initialize with consent
  if (typeof gtag !== 'undefined') {{
    gtag('js', new Date());
    gtag('config', '{self.measurement_id}');
  }}
}}

function declineCookies() {{
  localStorage.setItem('cookieConsent', 'declined');
  document.getElementById('cookieConsentBanner').style.display = 'none';
  updateConsentMode('denied', 'denied');
}}

function updateConsentMode(analytics, ads) {{
  if (typeof gtag !== 'undefined') {{
    gtag('consent', 'update', {{
      'analytics_storage': analytics,
      'ad_storage': ads
    }});
  }}
}}

// ページ読み込み時にチェック
document.addEventListener('DOMContentLoaded', checkCookieConsent);
</script>
"""
    
    def generate_gtm_code(self) -> str:
        """Google Tag Manager コードを生成"""
        if not self.gtm_id:
            return ""
        
        return f"""
<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
}})(window,document,'script','dataLayer','{self.gtm_id}');</script>
<!-- End Google Tag Manager -->
"""
    
    def generate_gtm_noscript(self) -> str:
        """Google Tag Manager noscript コードを生成"""
        if not self.gtm_id:
            return ""
        
        return f"""
<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={self.gtm_id}"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->
"""
    
    def should_track_user(self, user=None) -> bool:
        """ユーザーを追跡すべきかどうかを判定"""
        if not self.enabled:
            return False
        
        # 管理者追跡設定をチェック
        if user and hasattr(user, 'role') and user.role == 'admin':
            return self.track_admin
        
        return True
    
    def get_complete_tracking_code(self) -> Dict[str, str]:
        """完全なトラッキングコードを生成"""
        return {
            'head_code': self.generate_gtm_code() + self.generate_base_tracking_code(),
            'body_code': self.generate_gtm_noscript(),
            'enhanced_code': self.generate_enhanced_tracking_code(),
            'consent_banner': self.generate_cookie_consent_banner()
        }