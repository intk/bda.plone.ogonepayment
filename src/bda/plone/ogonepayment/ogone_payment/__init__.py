import urllib
import urllib2
import urlparse
import logging
from lxml import etree
from zExceptions import Redirect
from zope.i18nmessageid import MessageFactory
from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName
from bda.plone.payment.interfaces import IPaymentData

from bda.plone.shop.interfaces import IShopSettings
from zope.component import getUtility
from plone.registry.interfaces import IRegistry
from zope.i18n.interfaces import IUserPreferredLanguages
from status_codes import get_status_category, SUCCESS_STATUS
from bda.plone.orders import interfaces as ifaces
from bda.plone.orders.common import OrderData
from bda.plone.orders.common import get_order

from bda.plone.payment import (
    Payment,
    Payments,
)

from ZTUtils import make_query
from bda.plone.orders.common import get_order

from security import OgoneSignature

logger = logging.getLogger('bda.plone.payment')
_ = MessageFactory('bda.plone.payment')

CREATE_PAY_INIT_URL = "https://secure.ogone.com/ncol/test/orderstandard.asp"
PSPID = "pspid"
SHA_IN_PASSWORD = "pwd"
SHA_OUT_PASSWORD = "pwd"

class OgonePayment(Payment):
    pid = 'ogone_payment'
    label = _('ogone_payment', 'Ogone Payment')
    
    def init_url(self, uid):
        return '%s/@@ogone_payment?uid=%s' % (self.context.absolute_url(), uid)

class OgoneError(Exception):
    """Raised if SIX payment return an error.
    """

def shopmaster_mail(context):
    props = getToolByName(context, 'portal_properties')
    return props.site_properties.email_from_address

def perform_request(url, params=None):
    
    if params:
        query = urllib.urlencode(params)
        url = '%s?%s' % (url, query)
    return url

def create_pay_init(pspid, ordernumber, currency, amount, language, accepturl, declineurl, exceptionurl, cancelurl):
    
    params = {
        'PSPID': pspid,
        'ORDERID': ordernumber,
        'CURRENCY': currency,
        'AMOUNT': amount,
        'LANGUAGE': language,
        'ACCEPTURL': accepturl,
        'DECLINEURL': declineurl,
        'EXCEPTIONURL': exceptionurl,
        'CANCELURL': cancelurl,
    }

    signer = OgoneSignature(params, 'sha512', SHA_IN_PASSWORD)
    params['SHASIGN'] = signer.signature()

    return perform_request(CREATE_PAY_INIT_URL, params)

class OgonePay(BrowserView):
    def __call__(self):
        base_url = self.context.absolute_url()
        order_uid = self.request['uid']

        try:
            data = IPaymentData(self.context).data(order_uid)
            pspid = PSPID
            language = self.getLanguage()
            currency = data['currency']
            amount = data['amount']
            description = data['description']
            ordernumber = data['ordernumber']

            accepturl = "http://webshop-plone.intk.com/ogone_payment_success"

            declineurl = '%s/@@ogone_payment_failed?uid=%s' % (base_url, order_uid)
            exceptionurl = '%s/@@ogone_payment_failed?uid=%s' % (base_url, order_uid)
            cancelurl = '%s/@@ogone_payment_aborted?uid=%s' % (base_url, order_uid)

            redirect_url = create_pay_init(pspid, ordernumber, currency, amount, language, accepturl, declineurl, exceptionurl, cancelurl)

        except Exception, e:
            logger.error(u"Could not initialize payment: '%s'" % str(e))
            redirect_url = '%s/@@ogone_payment_failed?uid=%s' \
                % (base_url, order_uid)
        raise Redirect(redirect_url)

    def getLanguage(self):
        """
        Ogone requires en_EN or en_US language id
        We are parsing the request to get the right
        Note: took this code from getpaid.ogone (thanks)
        """
        languages = IUserPreferredLanguages(self.context.REQUEST)
        langs = languages.getPreferredLanguages()
        if langs:
            language = langs[0]
        else:
            plone_props = getToolByName(self.context, 'portal_properties')
            language = plone_props.site_properties.default_language
        language = language.split('-')
        if len(language) == 1:
            language.append(language[0])
        language = language[:2]
        return "_".join(language)

class OgonePaySuccess(BrowserView):
    def verify(self):
        #
        # Get Payment details
        #
        data = self.request.form
        ordernumber = data['orderID']
        
        if get_status_category(int(data['STATUS'])) != SUCCESS_STATUS:
            return False
        
        #
        # SHA passphrase verification
        #
        signer = OgoneSignature(data, 'sha512', SHA_OUT_PASSWORD)
        order_uid = IPaymentData(self.context).uid_for(ordernumber)
        payment = Payments(self.context).get('ogone_payment')

        if data['SHASIGN'] == signer.signature():
            payment.succeed(self.context, order_uid)
            order = OrderData(self.context, uid=order_uid)
            order.salaried = ifaces.SALARIED_YES
            return True
        else:
            payment.failed(self.context, order_uid)
            return False
    @property
    def shopmaster_mail(self):
        return shopmaster_mail(self.context)
    
    
    

class OgonePayFailed(BrowserView):
    def finalize(self):
        print "Ogone failed!"
        return True




    

        
