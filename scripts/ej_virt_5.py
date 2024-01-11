app('virtual_address_width 18', echo=False)
app('address_width 15', echo=False)
app('line_size_width 13', echo=False)
app('create Ej virt 5', echo=False)
app('policy LRU', echo=False)
app('name Physical', echo=False)
app('set_width 2', echo=False)
app('way_width 0', echo=False)
app('cache', echo=False)
app('name Cache', echo=False)
app('line_size_width 7', echo=False)
app('set_width 1', echo=False)
app('way_width 1', echo=False)
app('cache', echo=False)
app('line_size_width 13', echo=False)
app('name Virtual', echo=False)
app('virtual', echo=False)


#app('read 0x02000', echo=True)
#app('read 0x18000', echo=True)
#app('read 0x08000', echo=True)
#app('read 0x0c000', echo=True)

app('read 0x02880', echo=False)
app('read 0x18300', echo=False)
app('read 0x08700', echo=False)
app('read 0x0D380', echo=False)
app('reset_stats', echo=False)

app('show_state', echo=True)

app('read 0x08770', echo=True)
for i in range(0x2080, 0x209F):
    app(f'read {i}', echo=True)
for i in range(0x2880, 0x289F):
    app(f'read {i}', echo=True)
for i in range(0xD3F0, 0xD410):
    app(f'read {i}', echo=True)
for i in range(0x27000, 0x2701F):
    app(f'read {i}', echo=True)

app('show_state', echo=True)