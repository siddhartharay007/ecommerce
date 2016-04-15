from ecommerce.core.models import SiteConfiguration


def offline_context():
    site_configurations = SiteConfiguration.objects.all()
    for sc in site_configurations:
        yield {
            'theme_scss_path': sc.theme_scss_path,
        }

    # Alternately, we could scan the themes directory
    # for theme in ('default', 'edx'):
    #     yield {
    #         'theme_scss_path': 'sass/themes/{}.scss'.format(theme),
    #     }
