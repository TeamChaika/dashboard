#!/bin/bash
cd "$(dirname "$0")"
cd "../../"
git pull origin main
pm2 restart all