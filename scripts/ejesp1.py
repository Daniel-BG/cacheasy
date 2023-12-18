app('address_width 15', echo=True)
app('line_size_width 7', echo=True)
app('create Apartado A', echo=True)
app('name Memory', echo=True)
app('memory', echo=True)
app('name Cache', echo=True)
app('set_width 2', echo=True)
app('way_width 0', echo=True)
app('policy LRU', echo=True)
app('write_back True', echo=True)
app('write_allocate True', echo=True)
app('cache', echo=True)
app('read 0x6A00', echo=True)
app('read 0x2080', echo=True)
app('read 0x2100', echo=True)
app('read 0x1180', echo=True)
app('reset_stats', echo=True)

app('show_state', echo=True)
for dir_a in [0x2080, 0x2880, 0x03F0]:
    for i in range(32):
        app('read ' + str(dir_a + i), echo=True)

app('show_state stats', echo=True)
