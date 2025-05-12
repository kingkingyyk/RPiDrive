# FAQ

- How does official reference platform look like?

  I have Pi 4B with 4GB RAM + WD Blue 2.5" HDD in USB enclosure.

- Which Pi should I use?

  Pi 3B/3B+/4 are tested and supported. For best performance please use 4B with 2GB RAM or above. They have LAN that supports up to 1Gbps bandwidth.

- How many resource does RPi Drive use?

  In a Raspbian headless deployment, the operating system + RPi Drive will use around 600MB of RAM.

- Can I update files by other means other than RPiDrive itself?

  Not recommended. RPi Drive stores the file information in database & cache and provides it to the web interface. Not doing CRUD in web interface will result in dirty-state and reindexing is needed. You can fix this by using the `Perform index` function in storage provider menu. The indexing will also be performed periodically according to the `index.period` value specified in `config.yaml`.

- I experience bad upload/download performance.

  It is recommended to run your Pi on wired network. The embedded WiFi on Raspberry Pi 3/4 only provide up to ~12MB/s.

- Can I use other single board computer or even x86 computer?
  Sure! You can give them a try!
