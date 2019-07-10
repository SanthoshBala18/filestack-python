from filestack import config
from filestack.utils import requests
from filestack.mixins import CommonMixin
from filestack.mixins import ImageTransformationMixin


class Filelink(ImageTransformationMixin, CommonMixin):
    """
    Filelinks are object representations of Filestack Filehandles.
    You can perform all actions that is allowed through our REST API,
    including downloading, deleting, overwriting and retrieving metadata.
    You can also get image tags, SFW filters, and directly
    call any of our available transformations.
    """
    def __init__(self, handle, apikey=None, security=None):
        """
        Args:
            handle (str): The path of the file to wrap
            apikey (str): Filestack API key that may be required for some API calls
            security (:class:`filestack.Security`): Security object that will be used by default
               for all API calls
        """
        self.apikey = apikey
        self.handle = handle
        self.security = security

    def __repr__(self):
        return '<Filelink {}>'.format(self.handle)

    def _build_url(self, security=None):
        url_elements = [config.CDN_URL, self.handle]
        if security is not None:
            url_elements.insert(-1, security.as_url_string())
        return '/'.join(url_elements)

    def metadata(self, attributes_list, security=None):
        """
        Retrieves filelink's metadata.

        Args:
            attributes_list (list): The path of the file to wrap
            security (:class:`filestack.Security`): Security object that will be used
                to retrieve metadata

        >>> filelink.metadata(['size', 'filename'])
        {'filename': 'envelope.jpg', 'size': 171832}

        Returns:
            `dict`: A buffered writable file descriptor

        Raises:
            Exception: if API call fails, Exception will be raised
        """
        attr_string = '[{}]'.format(','.join(attributes_list))
        obj = self.add_transform_task('metadata', params={'self': None, 'p': attr_string})
        return requests.get(obj._build_url(security=security or self.security)).json()

    def delete(self, apikey=None, security=None):
        """
        Deletes filelink.

        Args:
            apikey (str): Filestack API key that will be used for this API call
            security (:class:`filestack.Security`): Security object that will be used
                to delete filelink

        Returns:
            None

        Raises:
            Exception: if API call fails, Exception will be raised
        """
        sec = security or self.security
        apikey = apikey or self.apikey

        if sec is None:
            raise Exception('Security is required to delete filelink')

        if apikey is None:
            raise Exception('Apikey is required to delete filelink')

        url = '{}/file/{}'.format(config.API_URL, self.handle)
        delete_params = {
            'key': apikey,
            'policy': sec.policy_b64,
            'signature': sec.signature
        }
        requests.delete(url, params=delete_params)

    def overwrite(self, *, filepath=None, url=None, file_obj=None, base64decode=False, security=None):
        """
        Overwrites filelink with new content

        Args:
            filepach (str): path to file
            url (str): file URL
            file_obj (io.BytesIO or similar): file-like object
            base64decode (bool): indicates if content should be decoded before it is stored
            security (:class:`filestack.Security`): Security object that will be used
                to overwrite filelink

        Note:
            This method only accepts keyword arguments.
            Out of filepath, url and file_obj only one should be provided.
        """
        sec = security or self.security
        if sec is None:
            raise Exception('Security is required to overwrite filelink')
        req_params = {
            'policy': sec.policy_b64,
            'signature': sec.signature,
            'base64decode': str(base64decode).lower()
        }

        request_url = '{}/file/{}'.format(config.API_URL, self.handle)
        if url:
            requests.post(request_url, params=req_params, data={'url': url})
        elif filepath:
            with open(filepath, 'rb') as f:
                files = {'fileUpload': ('filename', f, 'application/octet-stream')}
                requests.post(request_url, params=req_params, files=files)
        elif file_obj:
            files = {'fileUpload': ('filename', file_obj, 'application/octet-stream')}
            requests.post(request_url, params=req_params, files=files)
        else:
            raise Exception('filepath, file_obj or url argument must be provided')

        return self
