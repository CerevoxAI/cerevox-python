# Hippo Getting Started Guide

This guide demostrates how to use Cerevox Hippo.

## Table of Contents
- [Summary](#summary)
- [Steps](#steps)
  - [1. Create Folder](#1-create-folder)
  - [2. Upload Files into Folder](#2-upload-files-into-folder)
  - [3. Create Chat based on Folder](#3-create-chat-based-on-folder)
  - [4. Ask Questions to Chat](#4-ask-questions-to-chat)
- [Other Actions](#other-actions)

## Summary

1. Create Folder
2. Upload Files into Folder
3. Create Chat based on Folder
4. Ask Questions to Chat

## Steps

### 1. Create Folder

Chats are connected to a Folder, to reference data within.
So creating a Folder is the first step.

```python
# Start Hippo Client
client = Hippo(email="user@example.com", api_key="password")

# Create folder and upload files
folder_id = "docs"
client.create_folder(folder_id, "My Documents")
```

### 2. Upload Files into Folder

With a Folder, it needs to be populated with files.
This can come from file uploads, for files gotten from an URL.

```python
# Upload file to folder created
client.upload_file(folder_id, "/path/to/document.pdf")
```

### 3. Create Chat based on Folder

Now a Chat can be created, referencing this folder.
Chats contain the messages to/from Cerevox.

```python
# Create a chat for discussion, connected to folder
chat = client.create_chat(folder_id)
chat_id = chat["chat_id"]
```

### 4. Ask Questions to Chat

Finally questions can be asked to the Chat, and Cerevox will reference the data in connected Folder to give a reply.

```python
# Ask a question to chat
response = client.submit_ask(chat_id, "What is this document about?")
print(response["response"])
```

## Other Actions

Hippo has other functions for handling:
- Folders
- Files
- Chats
- Asks

Please see API reference [hippo.md](./apis/hippo.md) for details.
