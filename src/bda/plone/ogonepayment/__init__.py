from bda.plone.shop import message_factory as _

from zope import schema
from plone.supermodel import model
from zope.interface import Interface
from zope.interface import provider

from bda.plone.shop.interfaces import IShopSettingsProvider

#from zope.interface import Attribute


@provider(IShopSettingsProvider)
class IOgonePaymentSettings(model.Schema):
    
    model.fieldset( 'ogone',label=_(u'Ogone', default=u'Ogone'),
        fields=[
        'ogone_server_url',
        'ogone_sha_in_password',
        'ogone_sha_out_password',
        ],
    )
                   
    ogone_server_url = schema.ASCIILine(title=_(u'ogone_server_url', default=u'Server url'),
                 required=True
    )

    ogone_sha_in_password = schema.ASCIILine(title=_(u'ogone_sha_in_password', default=u'SHA in password'),
               required=True
    )
    
    ogone_sha_out_password = schema.ASCIILine(title=_(u'ogone_sha_out_password', default=u'SHA out password'),
               required=True
    )
    