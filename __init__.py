#!/bin/python 
# -*- coding: utf-8 -*- 
import os.path

from bs4 import BeautifulSoup
from binascii import hexlify, unhexlify

MIME_TO_EXTESION_MAPPING = {
    'image/png': '.png',
    'image/jpg': '.jpg',
    'image/jpeg': '.jpg',
    'image/gif': '.gif'
}

PROHIBITED_ENML_ELEMENTS = [
    "applet", "base", "basefont", "bgsound", "blink", "body", "button", "dir", "embed", "fieldset", 
    "form", "frame", "frameset", "head", "html", "iframe", "ilayer", "input", "isindex", "label", 
    "layer", "legend", "link", "marquee", "menu", "meta", "noframes", "noscript", "object", "optgroup", 
    "option", "param", "plaintext", "script", "select", "style", "textarea", "xml", "id", "class", 
    "onclick", "ondblclick", "on", "accesskey", "data", "dynsrc", "tabindex"
]

VALID_URL_PROTOCOLS = [
    "http", "https", "file"
]

# TODO: comparing existing resources
def get_image_objects(html, resource_path):
    soup = BeautifulSoup(html)
    images = soup.find_all('img')
    image_objects = []
    for image in images:
        image_src = image['src']
        alt_data = None
        if image.has_attr('alt'):
            alt_data = image['alt']
        if image_src[0] == '/':
            src_list = image_src.split('/')
            resource_url = os.path.join(resource_path,src_list[-1])
            with open(resource_url, "r") as f:
                image_data = f.read()
        else: 
            image_data = urlopen(image_src).read()
        mime_type = 'image/' + os.path.splitext(image_src)[1].split('.')[-1]
        image_objects.append((image_data, mime_type, alt_data))
    return image_objects

def HTMLToENML(content, **kwargs):
    """
    converts HTML string into ENML string
    """
    soup = BeautifulSoup(content)

    todos = soup.find_all(type="checkbox")
    for todo in todos:
        checkbox = soup.new_tag('en-todo')
        if todo.has_attr('checked'):
            checkbox['checked'] = todo['checked']
        todo.replace_with(checkbox)

    note = soup.find('body')
    if not note:
        note = soup.new_tag('en-note')
    else:
        note.name = 'en-note'

    images = soup.find_all('img')
    for image in images:
        image.extract()
    if 'resources' in kwargs:
        resources = kwargs['resources']
        for resource in resources:
            new_tag = soup.new_tag('en-media')
            new_tag['hash'] = hexlify(resource.data.bodyHash)
            new_tag['type'] = resource.mime
            if resource.alternateData:
                new_tag['alt'] = resource.alternateData
            note.append(new_tag)

    for tag in soup(PROHIBITED_ENML_ELEMENTS):
        tag.extract()

    enml = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
    enml += "<!DOCTYPE en-note SYSTEM \"http://xml.evernote.com/pub/enml2.dtd\">"
    enml += str(note)
    return enml

def ENMLToHTML(content, pretty=True, **kwargs):
    """
    converts ENML string into HTML string
    """
    soup = BeautifulSoup(content)
    
    todos = soup.find_all('en-todo')
    for todo in todos:
        checkbox = soup.new_tag('input')
        checkbox['type'] = 'checkbox'
        checkbox['disabled'] = 'true'
        if todo.has_attr('checked'):
            checkbox['checked'] = todo['checked']
        todo.replace_with(checkbox)

    if 'media_store' in kwargs:
        store = kwargs['media_store']
        all_media = soup.find_all('en-media')
        for media in all_media:
            resource_url = store.save(media['hash'], media['type'])
            # TODO: use different tags for different mime-types
            new_tag = soup.new_tag('img')
            new_tag['src'] = resource_url
            if media.has_attr('alt'):
                new_tag['alt'] = media['alt']
            media.replace_with(new_tag)
    
    note = soup.find('en-note')
    note.name = 'body'
    html = soup.new_tag('html')
    html.append(note)

    output = html.prettify().encode('utf-8') if pretty else str(html)
    return output


class MediaStore(object):
    def __init__(self, note_store, note_guid):
        """
        note_store: NoteStore object from EvernoteSDK
        note_guid: Guid of the note in which the resouces exist
        """
        self.note_store = note_store
        self.note_guid = note_guid

    def _get_resource_by_hash(self, hash_str):
        """
        get resource by its hash
        """
        hash_bin = unhexlify(hash_str)
        resource = self.note_store.getResourceByHash(self.note_guid, hash_bin, True, False, False);
        return resource.data.body

    def save(self, hash_str, mime_type):
        pass

class FileMediaStore(MediaStore):
    def __init__(self, note_store, note_guid, path):
        """
        note_store: NoteStore object from EvernoteSDK
        note_guid: Guid of the note in which the resouces exist
        path: The path to store media file
        """
        super(FileMediaStore, self).__init__(note_store, note_guid)
        self.path = os.path.abspath(path)
    
    def save(self, hash_str, mime_type):
        """
        save the specified hash and return the saved file's URL
        """
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        data = self._get_resource_by_hash(hash_str)
        file_name = hash_str + MIME_TO_EXTESION_MAPPING[mime_type]
        file_path = os.path.join(self.path, file_name)
        if not os.path.isfile(file_path):
            with open(file_path, "w") as f:
                f.write(data)
        return "file://" + file_path
        