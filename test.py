#!/usr/bin/python
# -*- coding: utf-8 -*-
from evernote.api.client import EvernoteClient, NoteStore, UserStore
import __init__ as enml

dev_token = 'changeme'
client = EvernoteClient(token=dev_token)
noteStore = client.get_note_store()
notebooks = noteStore.listNotebooks()

for notebook in notebooks:
    print "Notebook: %s" % notebook.name
    nfilter = NoteStore.NoteFilter(notebookGuid=notebook.guid)
    notes = noteStore.findNotes(nfilter, 0, 200)
    for note in notes.notes:
        print "└─%s" % note.title
        print "guid:%s"  % note.guid
        mediaStore = enml.FileMediaStore(noteStore, note.guid, 'resources/')
        content = noteStore.getNoteContent(note.guid)
        html = enml.ENMLToHTML(content, False, media_store=mediaStore)
        f = open(note.title + '.html', 'w')
        f.write(html)
        f.flush()
        f.close()
