from enum import Enum
import numpy as np

rng = np.random.default_rng()

ReplacementPolicy = Enum('ReplacementPolicy', ['FIFO', 'LRU', 'MRU', 'RANDOM'])

from colorama import Fore, Back, Style
def prettydir(addr, totalbits, setbits, bytebits, brackets=True, tagcol = Fore.RED):
    #calculate the toal amount of bits
    blockbits = totalbits - setbits - bytebits
    #convert addr to binary string of (totalbits)
    binstring = format(addr, '0'+str(totalbits)+'b')
    #separate bits
    blockstr = binstring[:blockbits]
    setstr = binstring[blockbits:blockbits+setbits]
    bytebits = binstring[blockbits+setbits:]

    if brackets:
        return '[' + tagcol + blockstr + Fore.GREEN + setstr + Fore.BLUE + bytebits + Style.RESET_ALL + ']'
    else:
        return tagcol + blockstr + Fore.GREEN + setstr + Fore.BLUE + bytebits + Style.RESET_ALL
    
prettytick = Fore.GREEN + "✔" + Style.RESET_ALL
prettyfail = Fore.RED + "✘" + Style.RESET_ALL
prettyright = Fore.YELLOW + "→" + Style.RESET_ALL
prettyleft = Fore.YELLOW + "←" + Style.RESET_ALL
prettyup = Fore.BLUE + "↑" + Style.RESET_ALL
prettyupyellow = Fore.YELLOW + "↑" + Style.RESET_ALL
prettydown = Fore.BLUE + "↓" + Style.RESET_ALL
prettydowndown = Fore.BLUE + "⯯" + Style.RESET_ALL
prettyswap = Fore.YELLOW + "⇆" + Style.RESET_ALL

"""prettytick = Fore.GREEN + "o" + Style.RESET_ALL
prettyfail = Fore.RED + "x" + Style.RESET_ALL
prettyright = Fore.YELLOW + ">" + Style.RESET_ALL
prettyleft = Fore.YELLOW + "<" + Style.RESET_ALL
prettyup = Fore.BLUE + "^" + Style.RESET_ALL
prettyupyellow = Fore.YELLOW + "^" + Style.RESET_ALL
prettydown = Fore.BLUE + "v" + Style.RESET_ALL
prettydowndown = Fore.BLUE + "vv" + Style.RESET_ALL
prettyswap = Fore.YELLOW + "<>" + Style.RESET_ALL"""


def bits_to_power(bits, unit):
    if bits < 10:
        return str(2**bits) + unit
    if bits < 20:
        return str(2**(bits - 10)) + "K" + unit
    if bits < 30:
        return str(2**(bits - 20)) + "M" + unit
    if bits < 40:
        return str(2**(bits - 30)) + "G" + unit
    if bits < 50:
        return str(2**(bits - 40)) + "T" + unit
    if bits < 60:
        return str(2**(bits - 50)) + "P" + unit
    return str(2**(bits - 60)) + "E" + unit




class MemorySystem:

    def __init__(self, address_width, line_size_width):
        self.address_width = address_width
        self.line_size_width = line_size_width
        self.levels = []
        self.last_level = None

    def add_main(self, name = "Main Memory"):
        if self.last_level is not None:
            raise Exception("Can't add main memory below a cache level")
        self.last_level = MainMemory(address_width = self.address_width, line_size_width = self.line_size_width, name = name)
        self.levels.append(self.last_level)

    def add_cache(self, name, set_width, way_width, replacement_policy, write_back, write_allocate, prefetch):
        if self.last_level is None:
            raise Exception("Add main memory before caches")
        new_cache = Cache(name = name, set_width = set_width, way_width = way_width, line_size_width = self.line_size_width, replacement_policy = replacement_policy, write_back = write_back, write_allocate = write_allocate, load_from = self.last_level, store_to = self.last_level, victim = None, address_width = self.address_width, prefetch = prefetch)
        self.last_level = new_cache
        self.levels.append(self.last_level)

    def add_victim(self, name, set_width, way_width, replacement_policy):
        if self.last_level is None or not hasattr(self.last_level, 'victim'):
            raise Exception("Can't add victim to an empty memory system or to main memory directly. Add a cache first")
        victim = Cache(name, set_width, way_width, line_size_width = self.line_size_width, replacement_policy = replacement_policy, address_width = self.address_width)
        self.last_level.victim = victim

    def read(self, init, end = None, step = None):
        if end is None:
            end = init
        if step is None:
            step = 1
        for i in range(init, end + 1, step):
            print(prettydir(i, self.address_width, 0, 0, tagcol = Fore.YELLOW) + Fore.YELLOW + " R Read Request" + Style.RESET_ALL)
            self.last_level.read(i)

    def write(self, init, end = None, step = None):
        if end is None:
            end = init
        if step is None:
            step = 1
        for i in range(init, end + 1, step):
            print(prettydir(i, self.address_width, 0, 0, tagcol = Fore.YELLOW) + Fore.YELLOW + " W Write Request" + Style.RESET_ALL)
            self.last_level.write(i)

    def reset_statistics(self):
        for level in self.levels:
            level.reset_statistics()

    def show_state(self, only_stats = False):
        for level in self.levels:
            if not only_stats:
                print(level)
            level.show_statistics()
            level.show_costs()




class CacheLine:

    def __init__(self, addr, tag, valid = True, dirty = False):
        self.dirty = dirty
        self.addr = addr
        self.tag = tag
        self.valid = valid
        
    def prettyprint(self, tag_width):
        string = prettydir(self.tag, tag_width, 0, 0, brackets = False)
        string += (Fore.BLACK if not self.valid else Fore.GREEN) + "V" + Style.RESET_ALL
        string += (Fore.BLACK if not self.dirty else Fore.YELLOW) + "D" + Style.RESET_ALL
        return string

class CacheStatistics:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.cost_hit = 1
        self.cost_miss = 200
        self.cost_through = 50
        
        self.read_hit = 0
        self.read_miss = 0

        self.write_hit = 0
        self.write_miss = 0
        self.write_through = 0

        self.victim_swap = 0
        self.victim_push = 0
        self.victim_evict = 0

        self.line_evict = 0
        self.line_miss = 0
        self.line_hit = 0
        self.line_pull = 0
        self.line_prefetch = 0

    def get_statistics(self):
        total_reads = self.read_hit + self.read_miss
        hitrate_read = float(self.read_hit) / float(total_reads) * 100.0 if total_reads > 0 else 0
        total_writes = self.write_hit + self.write_miss
        hitrate_write = float(self.write_hit) / float(total_writes) * 100.0 if total_writes > 0 else 0
        return f'Reads: [{Fore.GREEN}{self.read_hit}{Style.RESET_ALL}/{Fore.YELLOW}{total_reads}{Style.RESET_ALL}]({hitrate_read:.2f}) Writes: [{Fore.GREEN}{self.write_hit}{Style.RESET_ALL}/{Fore.YELLOW}{total_writes}{Style.RESET_ALL}]({hitrate_write:.2f}) [{Fore.LIGHTMAGENTA_EX}{self.write_through}{Style.RESET_ALL}{prettyup}]' + \
            " [Blocks: " + Fore.GREEN + str(self.line_hit) + Style.RESET_ALL + "/" + Fore.RED + str(self.line_miss) + " " + prettydown + str(self.line_pull) + "(" + prettydowndown + str(self.line_prefetch) + ") " + prettyup + str(self.line_evict) + "]" + \
            " [Victim: " + prettyswap + str(self.victim_swap) + " " + prettyright + str(self.victim_push) + " " + prettyupyellow + str(self.victim_evict) + "]"
            
    def get_cost(self):
        total_hit = self.read_hit + self.write_hit
        cost_hit = total_hit * self.cost_hit
        total_miss = self.read_miss + self.write_miss
        cost_miss = total_miss * self.cost_miss
        total_through = self.write_through
        cost_through = total_through * self.cost_through
        total_cost = cost_hit + cost_miss + cost_through
        return f'Cost: {Fore.YELLOW}{total_cost}{Style.RESET_ALL} {prettyright} {Fore.GREEN}{total_hit}{Style.RESET_ALL} hits: [{Fore.YELLOW}{cost_hit}{Style.RESET_ALL}] | {Fore.RED}{total_miss}{Style.RESET_ALL} misses: [{Fore.YELLOW}{cost_miss}{Style.RESET_ALL}] | {Fore.BLUE}{total_through}{Style.RESET_ALL} through: [{Fore.YELLOW}{cost_through}{Style.RESET_ALL}]'


class MainMemory:

    def __init__(self, address_width, line_size_width, name = "Main memory"):
        self.name = name
        self.address_width = address_width
        self.line_size_width = line_size_width
        self.statistics = CacheStatistics()
        
    def __contains__(self, key):
        return key < (1 << self.address_width)

    def get_block(self, addr):
        return addr >> self.line_size_width

    def read(self, addr):
        self.statistics.read_hit += 1
        print(prettydir(addr, self.address_width, 0, self.line_size_width) + " " + prettydown +  (" Block 0x%0x read from main memory" % self.get_block(addr)))
        return True

    def write(self, addr):
        self.statistics.write_hit += 1
        print(prettydir(addr, self.address_width, 0, self.line_size_width) + " " + prettyup + (" Block 0x%0x written to main memory" % self.get_block(addr)))
        return True

    def write_line(self, line):
        return self.write(line.addr)

    def show_statistics(self):
        print(self.name + ": " + self.statistics.get_statistics())
        
    def show_costs(self):
        print(self.name + ": " + self.statistics.get_cost())

    def reset_statistics(self):
        self.statistics.reset()
        
    def reset_costs(self, cost_hit, cost_miss, cost_through):
        self.statistics.cost_hit = cost_hit
        self.statistics.cost_miss = cost_miss
        self.statistics.cost_through = cost_through
        
    def __str__(self):
        return "%s: %s (%s of %s)" % (self.name, bits_to_power(self.address_width, 'B'), bits_to_power(self.address_width-self.line_size_width, ' Blocks'), bits_to_power(self.line_size_width, 'B'))


class Cache:

    def __init__(self, name, set_width, way_width, line_size_width, replacement_policy = ReplacementPolicy.LRU, write_back = True, write_allocate = True, load_from = None, store_to = None, victim = None, address_width = 32, prefetch = None):
        self.replacement_policy = replacement_policy

        #Log base two of the number of sets, ways and bytes per line
        self.set_width = set_width              
        self.way_width = way_width              
        self.line_size_width = line_size_width  

        #write back policy (only write when evicted)
        #if disabled it is write-through (write always to cache and behind (avoid dirty)
        self.write_back = write_back        
        #write allocate policy. If enabled, blocks are brought to cache when writing
        #if not enabled, blocks are written to main memory
        self.write_allocate = write_allocate
        #prefetch, when a block fails to be located, bring the X ones as well
        self.prefetch = prefetch

        self.load_from = load_from  #memory where we load from. Might be None (e.g:victim)
        self.store_to = store_to    #memory where we store to. Might be None (e.g:victim)
        self.victim = victim        #victim cache. Might be None (e.g:mainmemory)

        #for pretty printing and statistics
        self.address_width = address_width 
        self.name = name
        self.statistics = CacheStatistics()

        #initialize set structure: list of lists
        self.set_data = []
        for i in range(2**self.set_width):
            set_info = []
            for i in range(2**self.way_width):
                set_info.append(CacheLine(0, 0, False, False))
            self.set_data.append(set_info)


    def get_set_idx(self, addr):
        block = addr >> self.line_size_width
        return block % (2**self.set_width)

    def get_set(self, addr):
        return self.set_data[self.get_set_idx(addr)]
    
    def get_tag(self, addr):
        block = addr >> self.line_size_width
        tag_num = block >> self.set_width
        return tag_num

    def __contains__(self, key):
        candidate_set = self.get_set(key)
        for line in candidate_set:
            if line.valid and line.tag == self.get_tag(key):
                return True
        return False
        

    def read(self, addr):
        if addr in self:
            self.statistics.read_hit += 1
        else:
            self.statistics.read_miss += 1
        self.get(addr)
        self._update(addr) #update LRU, etc

    def write(self, addr):
        #allocate space before updating
        if self.write_allocate:
            if addr in self:
                self.statistics.write_hit += 1
            else:
                self.statistics.write_miss += 1

            self.get(addr)
            self._update(addr, dirty=True) #update LRU, etc
        else: 
            #if the block is here, write it
            if addr in self:
                self.statistics.write_hit += 1
                self.get(addr)
                self._update(addr, dirty=True) #update LRU, etc
            #if not, write next level
            else:
                self.statistics.write_through += 1
                self.store_to.write(addr)


    #gets an address for this cache. Internal statistics are updated, and data is brought if needed
    def get(self, addr, prefetched = 0):
        if addr in self: #Data found!
            print(prettydir(addr, self.address_width, self.set_width, self.line_size_width) + " " + prettytick + " Tag 0x%0x in %s set 0x%0x" % (self.get_tag(addr), self.name, self.get_set_idx(addr)))
            self.statistics.line_hit += 1
            return True
        else: #data not found
            self.statistics.line_miss += 1
            if self.victim:
                if addr in self.victim: #data found in victim
                    print(prettydir(addr, self.address_width, self.set_width, self.line_size_width) + " " + prettytick + " Addr 0x%0x in %s" % (addr, self.victim.name))
                    line_from_cache = self.allocate_for(addr)
                    line_from_victim = self.victim.extract(addr)
                    self.victim.write_line(line_from_cache)
                    self.write_line(line_from_victim)
                    print(prettydir(line_from_cache.addr, self.address_width, self.set_width, self.line_size_width) + " " + prettyright +  " Tag 0x%0x from %s to %s" % (self.get_tag(line_from_cache.addr), self.name, self.victim.name))
                    print(prettydir(line_from_victim.addr, self.address_width, self.set_width, self.line_size_width) + " " + prettyleft + " Tag 0x%0x from %s to %s" % (self.get_tag(line_from_victim.addr), self.victim.name, self.name))
                    self.statistics.victim_swap += 1
                    return True
                else: #data not in victim
                    print(prettydir(addr, self.address_width, self.set_width, self.line_size_width) + " " + prettyfail + " Tag 0x%0x not in %s" % (self.get_tag(addr), self.name))
                    line_from_cache = self.allocate_for(addr)
                    if line_from_cache.valid: #needs to go to victim cache
                        line_from_victim = self.victim.allocate_for(line_from_cache.addr)
                        self.victim.write_line(line_from_cache)
                        self.statistics.victim_push += 1
                        if line_from_victim.valid and line_from_victim.dirty: #needs to go to upper level
                            print(prettydir(line_from_victim.addr, self.address_width, self.set_width, self.line_size_width) + " " + prettyright +  " Tag 0x%0x from %s to %s" % (self.get_tag(line_from_victim.addr), self.victim.name, self.store_to.name))
                            self.store_to.write_line(line_from_victim)
                            self.statistics.victim_evict += 1
                        print(prettydir(line_from_cache.addr, self.address_width, self.set_width, self.line_size_width) + " " + prettyright +  " Tag 0x%0x from %s to %s" % (self.get_tag(line_from_cache.addr), self.name, self.victim.name))

            else: #no victim cache
                print(prettydir(addr, self.address_width, self.set_width, self.line_size_width) + " " + prettyfail + " Tag 0x%0x not in %s set 0x%0x" % (self.get_tag(addr), self.name, self.get_set_idx(addr)))
                line_from_cache = self.allocate_for(addr)
                if line_from_cache.valid and line_from_cache.dirty:
                    self.statistics.line_evict += 1
                    self.store_to.write_line(line_from_cache)
                    print(prettydir(line_from_cache.addr, self.address_width, self.set_width, self.line_size_width) + " " + prettyright +  " Tag 0x%0x from %s to %s" % (self.get_tag(line_from_cache.addr), self.name, self.store_to.name))


            #ask higher level for data since we did not find it inside or in victim
            self.statistics.line_pull += 1
            self.load_from.read(addr)
            if addr not in self.load_from:
                print("An address was requested to a memory that does not have it nor does it have a higher order memory connected")
                return False
            print(prettydir(addr, self.address_width, self.set_width, self.line_size_width) + " " + prettyleft + " Tag 0x%0x from %s to %s set 0x%0x" % (self.get_tag(addr), self.load_from.name, self.name, self.get_set_idx(addr)))
            self._write(addr, dirty=False)

            if self.prefetch is not None:
                if prefetched >= self.prefetch:
                    return True
                else:
                    self.statistics.line_prefetch += 1
                    return self.get(addr + 2**self.line_size_width, prefetched + 1)
            else:
                return True

        self._update(addr)

    def write_line(self, line):
        self._write(line.addr, line.dirty)

    def _write(self, addr, dirty=True):
        if addr in self:
            raise Exception("Adding an existing element")

        candidate_set = self.get_set(addr)

        match self.replacement_policy:
            case ReplacementPolicy.RANDOM:
                placed = False
                for (i, elem) in enumerate(candidate_set):
                    if not elem.valid:
                        elem = CacheLine(addr, self.get_tag(addr), valid=True, dirty=dirty)
                        placed = True
                        break

                if not placed:
                    raise Exception("ERROR")
            case _:
                #chech that there is empty space
                placed = False
                for (i, line) in enumerate(candidate_set):
                    if not line.valid:
                        placed = True
                        candidate_set[0] = CacheLine(addr, self.get_tag(addr), valid=True, dirty=dirty)
                        break

                if not placed:
                    raise Exception("ERROR")

                #update policy
                self._update(addr)

                
    def _update(self, addr, dirty=False):
        candidate_set = self.get_set(addr)
        for (i, line) in enumerate(candidate_set):
            if line.tag == self.get_tag(addr):
                match self.replacement_policy:
                    case ReplacementPolicy.LRU | ReplacementPolicy.MRU:
                        elem = candidate_set.pop(i)
                        elem.dirty = dirty
                        candidate_set.insert(0, elem)
                    case _:
                        pass
                        #doesnt matter for the rest
                return True
        return False
        self.statistics.writes += 1
        
    def allocate_for(self, addr, force=False):
        #can return an invalid line!! be careful
        if addr in self and not force:
            raise Exception("Cannot allocate for already existing address")

        candidate_set = self.get_set(addr)
        
        outgoing = None
        match self.replacement_policy:
            case ReplacementPolicy.RANDOM:
                index = rng.randint(0, 2**self.way_width-1)
                outgoing = candidate_set[index]
                candidate_set[index] = CacheLine(0, 0, False, False)
            case ReplacementPolicy.FIFO | ReplacementPolicy.LRU:
                outgoing = candidate_set.pop()
                candidate_set.insert(0, CacheLine(0, 0, False, False))
            case ReplacementPolicy.MRU:
                outgoing = candidate_set.pop(0)
                candidate_set.push(CacheLine(0, 0, False, False))
            case _:
                raise Exception("Using an unsupported policy")

        return outgoing

    def extract(self, addr):
        candidate_set = self.get_set(addr)
        elem = None
        for (i, line) in enumerate(candidate_set):
            if line.tag == self.get_tag(addr):
                elem = candidate_set[i]
                candidate_set[i] = CacheLine(0,0,False,False)
                break
        #Must return a CacheLine otherwise throw error
        if elem is None:
            raise Exception("Did not find line for extraction")
        return elem

    def __str__(self):
        setstr = []
        for (i, seti) in enumerate(self.set_data):
            linestr = []
            for line in seti:
                #linestr.append(line.prettyprint(self.address_width - self.line_size_width - self.set_width))
                hex_fmt = '0' + str((self.address_width + 3) // 4) + 'x'
                base_addr = line.tag * (2**(self.line_size_width + self.set_width)) + i*2**self.line_size_width
                high_addr = base_addr + 2**(self.line_size_width) - 1
                linestr.append(('%s [' + Fore.YELLOW + '0x%s-0x%s' + Style.RESET_ALL + ']') % (line.prettyprint(self.address_width - self.line_size_width - self.set_width), format(base_addr, hex_fmt), format(high_addr, hex_fmt)))


            setstr.append(",".join(linestr) + " " + prettydir(i << self.line_size_width, self.line_size_width + self.set_width, self.set_width, self.line_size_width))
                        
        if self.victim:
            return "\n".join(setstr) + "\n" + str(self.victim)
        else:
            return "\n".join(setstr)


    def show_statistics(self):
        print(self.name + ": " + self.statistics.get_statistics())
    
    def show_costs(self):
        print(self.name + ": " + self.statistics.get_cost())

    def reset_statistics(self):
        self.statistics.reset()
        
    def reset_costs(self, cost_hit, cost_miss, cost_through):
        self.statistics.cost_hit = cost_hit
        self.statistics.cost_miss = cost_miss
        self.statistics.cost_through = cost_through



import cmd2

class Cacheasy(cmd2.Cmd):
    """Simple command processor example."""

    def __init__(self):
        self.memsys = None
        self.address_width = 32
        self.line_size_width = 8
        self.memory_name = "MEM"
        self.set_width = 3
        self.way_width = 3
        self.replacement_policy = ReplacementPolicy.LRU
        self.write_back = True
        self.write_allocate = True
        self.prefetch = 0
        
        self.cost_hit = 1
        self.cost_miss = 200
        self.cost_through = 50
        super().__init__()
        
        
    def parse_number(self, input_str):
        try:
            # Try to parse as a decimal number
            result = int(input_str, 10)
        except ValueError:
            try:
                # If parsing as a decimal fails, try parsing as a hexadecimal number
                result = int(input_str, 16)
            except ValueError:
                # If both attempts fail, the input is not a valid number
                raise ValueError("Invalid number format")
        return result
    
    def do_read(self, args):
        """read <address> [final_address] [word_size]
        Requests a read from memory. If final address 
        is specified, it reads the whole range (inclusive).
        If word_size is specified, the requests are performed
        only for multiples of that size"""
        if not args:
            print("An address must be specified")
        
        parsed_args = [self.parse_number(s) for s in args.split()]

        if len(parsed_args) == 1:
            self.memsys.read(parsed_args[0])
        elif len(parsed_args) == 2:
            self.memsys.read(parsed_args[0], parsed_args[1])
        elif len(parsed_args) == 3:
            self.memsys.read(parsed_args[0], parsed_args[1], parsed_args[2])
        else:
            print("Too many args")
            
    def do_write(self, args):
        """write <address> [final_address] [word_size]
        Requests a write to memory. If final address 
        is specified, it writes the whole range (inclusive).
        If word_size is specified, the requests are performed
        only for multiples of that size"""
        if not args:
            print("An address must be specified")
        
        parsed_args = [self.parse_number(s) for s in args.split()]

        if len(parsed_args) == 1:
            self.memsys.write(parsed_args[0])
        elif len(parsed_args) == 2:
            self.memsys.write(parsed_args[0], parsed_args[1])
        elif len(parsed_args) == 3:
            self.memsys.write(parsed_args[0], parsed_args[1], parsed_args[2])
        else:
            print("Too many args")

    def do_show_config(self, args):
        print(f"Address width: {self.address_width}")
        print(f"Set width: {self.set_width}")
        print(f"Way width: {self.way_width}")
        print(f"Line size width: {self.line_size_width}")
        print(f"Memory name: {self.memory_name}")
        print(f"Memory policy: {self.replacement_policy}")
        print(f"Write back: {self.write_back}")
        print(f"Write allocate: {self.write_allocate}")
        print(f"Prefetch blocks: {self.prefetch}")

    def do_show_state(self, args):
        self.memsys.show_state(only_stats=args == "stats")

    def parseint(self, oldval, args, name=""):
        try:
            data = int(args)
            print(f"{Fore.GREEN}{name}{Style.RESET_ALL}set to {Fore.YELLOW}{data}{Style.RESET_ALL}")
            return data
        except Exception as e:
            print(e)
            return oldval
    
    def parsebool(self, oldval, args, name=""):
        try:
            data = args == "True"
            print(f"{Fore.GREEN}{name}{Style.RESET_ALL}set to {Fore.YELLOW}{data}{Style.RESET_ALL}")
            return data
        except Exception as e:
            print(e)
            return oldval

    def parsestr(self, oldval, args, name=""):
        try:
            if args is None:
                raise Exception()
            data = str(args)
            print(f"{Fore.GREEN}{name}{Style.RESET_ALL}set to {Fore.YELLOW}{data}{Style.RESET_ALL}")
            return data
        except Exception as e:
            print(e)
            return oldval

    def parsepolicy(self, oldval, args, name=""):
        try:
            data = ReplacementPolicy[str(args)]
            print(f"{Fore.GREEN}{name}{Style.RESET_ALL}set to {Fore.YELLOW}{data}{Style.RESET_ALL}")
            return data
        except Exception as e:
            print(e)
            return oldval

    def do_address_width(self, args):
        self.address_width = self.parseint(self.address_width, args, name="Address width ")
    def do_set_width(self, args):
        self.set_width = self.parseint(self.set_width, args, name="Set width ")
    def do_way_width(self, args):
        self.way_width = self.parseint(self.way_width, args, name="Way width ")
    def do_line_size_width(self, args):
        self.line_size_width = self.parseint(self.line_size_width, args, name="Line size width ")
    def do_prefetch(self, args):
        self.prefetch = self.parseint(self.prefetch, args, name="Prefetch ")
    def do_name(self, args):
        self.memory_name = self.parsestr(self.memory_name, args, name="Memory name ")
    def do_write_back(self, args):
        self.write_back = self.parsebool(self.write_back, args, name="Write back ")
    def do_write_allocate(self, args):
        self.write_allocate = self.parsebool(self.write_allocate, args, name="Write allocate ")
    def do_policy(self, args):
        self.replacement_policy = self.parsepolicy(self.replacement_policy, args, name="Replacement policy ")
    def do_cost_hit(self, args):
        self.cost_hit = self.parseint(self.cost_hit, args, name="Cost hit ")
    def do_cost_miss(self, args):
        self.cost_miss = self.parseint(self.cost_miss, args, name="Cost miss ")
    def do_cost_through(self, args):
        self.cost_through = self.parseint(self.cost_through, args, name="Cost through ")
    def do_reset_stats(self, args):
        self.memsys.reset_statistics()
    def do_reset_costs(self, args):
        self.memsys.last_level.reset_costs(cost_hit = self.cost_hit, cost_miss = self.cost_miss, cost_through = self.cost_through)
        

    def do_create(self, args):
        """create
        Create a memory system with the configured address width and line width
        """
        self.memsys = MemorySystem(self.address_width, self.line_size_width)
        self.poutput(f"{Fore.BLUE}{Back.GREEN}Created memory system {Fore.RED}{args}{Style.RESET_ALL}")

    def do_memory(self, args):
        """memory
        Create the main memory with the configured parameters"""
        if self.memsys is None:
            print("Initialize memory first")
        else:
            try:
                self.memsys.add_main(name = self.memory_name)
            except Exception as e:
                print(e)
                return
        print(f"{Fore.BLUE}Added main memory{Style.RESET_ALL}")

    def do_cache(self, args):
        """cache 
        Create a cache level with the configured parameters"""
        if self.memsys is None:
            print("Initialize memory first")
        else:
            try:
                self.memsys.add_cache(name = self.memory_name, set_width = self.set_width, way_width = self.way_width, replacement_policy = self.replacement_policy, write_back = self.write_back, write_allocate = self.write_allocate, prefetch = self.prefetch)
            except Exception as e:
                print(e)
                return
        print(f"{Fore.BLUE}Added cache level{Style.RESET_ALL}")

    def do_victim(self, args):
        """victim
        Create a victim cache with the configured parameters"""
        if self.memsys is None:
            print("Initialize memory first")
        else:
            try:
                self.memsys.add_victim(name = self.memory_name, set_width = self.set_width, way_width = self.way_width, replacement_policy = self.replacement_policy)
            except Exception as e:
                print(e)
                return
        print(f"{Fore.BLUE}Added victim cache{Style.RESET_ALL}")
    
    def do_quit(self, line):
        return True

    def do_EOF(self, line):
        return True
    
    def postloop(self):
        print

if __name__ == '__main__':
    Cacheasy().cmdloop()
    
    
"""
    write_allocate: reserves memory when writing (brings block)
    no write_allocate: does not reserve memory if the block is not in cache (just writes to upper memory)

    TODO:
    write_back: only write a block when evicted
    write_through: writes all the hierarchy when dirty, no waiting for eviction

    TODO:
    differentiate between line read/writes and word read/writes since it is different!!!
    
    TODO:
    implement a simple virtual memory system with TLB. 
"""