import os

from auth_backends.urls import auth_urlpatterns
from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.views.generic import TemplateView

from ecommerce.core import views as core_views
from ecommerce.core.url_utils import get_lms_dashboard_url
from ecommerce.core.views import LogoutView
from ecommerce.extensions.urls import urlpatterns as extensions_patterns


def handler403(_):
    """Redirect unauthorized users to the LMS student dashboard.

    Removing URLs isn't the most elegant way to hide Oscar's front-end from
    public view. It would require revising templates and parts of the Oscar core
    which assume that these URLs exist. However, a clean way to, in effect,
    disable these URLs is to only make them available to users with staff
    permissions, the same protection used to guard the management dashboard from
    public access.

    This minimally invasive approach allows us to protect Oscar's front-end
    without sacrificing any internal functionality. Users not authorized to view
    Oscar's front-end are redirected to the LMS student dashboard, as one would
    usually be after signing into the LMS.
    """
    return redirect(get_lms_dashboard_url())


admin.autodiscover()

js_info_dict = {
    'packages': ('courses',),
}

# Use the same auth views for all logins, including those originating from the browseable API.
AUTH_URLS = auth_urlpatterns + [
    url(r'^logout/$', LogoutView.as_view(), name='logout'),
]

urlpatterns = [
    url('', include(AUTH_URLS)),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^auto_auth/$', core_views.AutoAuth.as_view(), name='auto_auth'),
    url(r'^api-auth/', include(AUTH_URLS, namespace='rest_framework')),
    url(r'^api-docs/', include('rest_framework_swagger.urls')),
    url(r'^courses/', include('ecommerce.courses.urls', namespace='courses')),
    url(r'^credit/', include('ecommerce.credit.urls', namespace='credit')),
    url(r'^coupons/', include('ecommerce.coupons.urls', namespace='coupons')),
    url(r'^health/$', core_views.health, name='health'),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^jsi18n/$', 'django.views.i18n.javascript_catalog', js_info_dict),
]

# Install Oscar extension URLs
urlpatterns += extensions_patterns

robots = TemplateView.as_view(template_name='robots.txt', content_type='text/plain')
urlpatterns += [
    url(r'^robots\.txt$', robots, name='robots')
]

if settings.DEBUG and settings.MEDIA_ROOT:  # pragma: no cover
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )

if settings.DEBUG:  # pragma: no cover
    urlpatterns += [
        url(r'^403/$', handler403, name='403'),
        url(r'^404/$', 'django.views.defaults.page_not_found', name='404'),
        url(r'^500/$', 'django.views.defaults.server_error', name='500'),
        url(r'^bootstrap/$', TemplateView.as_view(template_name='bootstrap-demo.html')),
    ]
    # Allow error pages to be tested

    if os.environ.get('ENABLE_DJANGO_TOOLBAR', False):
        import debug_toolbar  # pylint: disable=import-error, wrong-import-position,wrong-import-order

        urlpatterns += [
            url(r'^__debug__/', include(debug_toolbar.urls))
        ]
