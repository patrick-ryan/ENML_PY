#!/bin/python 
# -*- coding: utf-8 -*- 
import os.path
from bs4 import BeautifulSoup

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

def HTMLToENML(content):
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

    images = soup.find_all('img')
    for image in images:
        new_tag = soup.new_tag('en-media')
        hash_str, type_ext = image['src'].rsplit("/",1)[1].rsplit(".",1)
        new_tag['hash'] = hash_str
        new_tag['type'] = "image/" + type_ext
        if image.has_attr('alt'):
            new_tag['alt'] = image['alt']
        image.replace_with(new_tag)

    body = soup.find('body')
    body.name = 'en-note'
    [tag.extract() for tag in soup(PROHIBITED_ENML_ELEMENTS)]
    note = str(body)
    return note

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
    html = soup.new_tag('html')
    html.append(note)
    note.name = 'body'

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
        hash_bin = hash_str.decode('hex')
        resource = self.note_store.getResourceByHash(self.note_guid, hash_bin, True, False, False);
        return resource.data.body

    def save(self, hash_str, mime_type):
        pass

class FileMediaStore(MediaStore):
    def __init__(self, note_store, note_guid, path):
        """
        note_store: NoteStore object from EvernoteSDK
        note_guid: Guid of the note in which the resouces exist
        """
        super(FileMediaStore, self).__init__(note_store, note_guid)
        self.path = path
    
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
        