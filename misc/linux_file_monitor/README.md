使用方法

```
# 自动做文件备份
python monitor.py -w /home/monitor_dir -b /home/backup_dir
# 不做文件备份
python monitor.py -w /home/monitor_dir -b /home/backup_dir -d

# 如果修改备份文件夹中的文件，会自动同步到监控文件夹中
```
