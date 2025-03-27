#!/bin/bash


eval "$(ssh-agent -s)"
ssh-add github_ssh
ssh -T git@github.com
git remote set-url origin git@github.com:dgleeson3/flask_blog.git
git push -u origin master