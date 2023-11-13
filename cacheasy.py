from enum import Enum
import numpy as np

rng = np.random.default_rng()

ReplacementPolicy = Enum('ReplacementPolicy', ['FIFO', 'LRU', 'MRU', 'RANDOM'])

from colorama import Fore, Style
def prettydir(addr, totalbits, setbits, bytebits, brackets=True):
    
    #calculate the toal amount of bits
    blockbits = totalbits - setbits - bytebits
    #convert addr to binary string of (totalbits)
    binstring = format(addr, '0'+str(totalbits)+'b')
    #separate bits
    blockstr = binstring[:blockbits]
    setstr = binstring[blockbits:blockbits+setbits]
    bytebits = binstring[blockbits+setbits:]

    if brackets:
        return '[' + Fore.RED + blockstr + Fore.GREEN + setstr + Fore.BLUE + bytebits + Style.RESET_ALL + ']'
    else:
        return Fore.RED + blockstr + Fore.GREEN + setstr + Fore.BLUE + bytebits + Style.RESET_ALL
    
prettytick = Fore.GREEN + "✔" + Style.RESET_ALL
prettyfail = Fore.RED + "✘" + Style.RESET_ALL
prettyright = Fore.YELLOW + "→" + Style.RESET_ALL
prettyleft = Fore.YELLOW + "←" + Style.RESET_ALL
prettyup = Fore.BLUE + "↑" + Style.RESET_ALL
prettydown = Fore.BLUE + "↓" + Style.RESET_ALL

def unimperror():
    raise NotImplementedError






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
        self.hits = 0
        self.misses = 0
        self.reads = 0
        self.writes = 0


class MainMemory:

    def __init__(self, address_width, line_size_width, name = "Main memory"):
        self.name = name
        self.address_width = address_width
        self.line_size_width = line_size_width

    def get_block(self, addr):
        return addr >> self.line_size_width

    def read(self, addr):
        print(prettydir(addr, self.address_width, 0, self.line_size_width) + " " + prettydown +  (" Block %s read from main memory" % str(self.get_block(addr))))
        return True

    def write(self, addr):
        print(prettydir(addr, self.address_width, 0, self.line_size_width) + " " + prettyup + (" Block %s written to main memory" % str(self.get_block(addr))))
        return True

    def write_line(self, line):
        return self.write(line.addr)


class Cache:

    def __init__(self, name, set_width, way_width, line_size_width, replacement_policy = ReplacementPolicy.LRU, write_back = True, write_allocate = True, load_from = None, store_to = None, victim = None, address_width = 32):
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
        self.get(addr)
        self.statistics.reads += 1
        self._update(addr) #update LRU, etc

    def write(self, addr):
        self.get(addr)
        self._update(addr, dirty=True) #update LRU, etc

    #gets an address for this cache. Internal statistics are updated, and data is brought if needed
    def get(self, addr):
        if addr in self: #Data found!
            self.statistics.hits += 1 
            print(prettydir(addr, self.address_width, self.set_width, self.line_size_width) + " " + prettytick + " Tag %d in %s" % (self.get_tag(addr), self.name))
            return True
        else: #data not found

            if self.victim:
                if addr in self.victim: #data found in victim
                    print(prettydir(addr, self.address_width, self.set_width, self.line_size_width) + " " + prettytick + " Tag %d in %s" % (self.get_tag(addr), self.victim.name))
                    line_from_cache = self.allocate_for(addr)
                    line_from_victim = self.victim.extract(addr)
                    self.victim.write_line(line_from_cache)
                    self.write_line(line_from_victim)
                    print(prettydir(line_from_cache.addr, self.address_width, self.set_width, self.line_size_width) + " " + prettyright +  " Tag %d from %s to %s" % (self.get_tag(line_from_cache.addr), self.name, self.victim.name))
                    print(prettydir(line_from_victim.addr, self.address_width, self.set_width, self.line_size_width) + " " + prettyleft + " Tag %d from %s to %s" % (self.get_tag(line_from_victim.addr), self.victim.name, self.name))
                    return True
                else: #data not in victim
                    print(prettydir(addr, self.address_width, self.set_width, self.line_size_width) + " " + prettyfail + " Tag %d not in %s" % (self.get_tag(addr), self.name))
                    line_from_cache = self.allocate_for(addr)
                    if line_from_cache.valid: #needs to go to victim cache
                        line_from_victim = self.victim.allocate_for(line_from_cache.addr)
                        self.victim.write_line(line_from_cache)
                        if line_from_victim.valid and line_from_victim.dirty: #needs to go to upper level
                            print(prettydir(line_from_victim.addr, self.address_width, self.set_width, self.line_size_width) + " " + prettyright +  " Tag %d from %s to %s" % (self.get_tag(line_from_victim.addr), self.victim.name, self.store_to.name))
                            self.store_to.write_line(line_from_victim)
                        print(prettydir(line_from_cache.addr, self.address_width, self.set_width, self.line_size_width) + " " + prettyright +  " Tag %d from %s to %s" % (self.get_tag(line_from_cache.addr), self.name, self.victim.name))

            else: #no victim cache
                print(prettydir(addr, self.address_width, self.set_width, self.line_size_width) + " " + prettyfail + " Tag %d not in %s" % (self.get_tag(addr), self.name))
                line_from_cache = self.allocate_for(addr)
                if line_from_cache.valid and line_from_cache.dirty:
                    self.store_to.write_line(line_from_cache)
                    print(prettydir(line_from_cache.addr, self.address_width, self.set_width, self.line_size_width) + " " + prettyright +  " Tag %d from %s to %s" % (self.get_tag(line_from_cache.addr), self.name, self.store_to.name))


            #ask higher level for data since we did not find it inside or in victim
            if not self.load_from.read(addr):
                print("An address was requested to a memory that does not have it nor does it have a higher order memory connected")
                return False

            print(prettydir(addr, self.address_width, self.set_width, self.line_size_width) + " " + prettyleft + " Tag %d from %s to %s" % (self.get_tag(addr), self.load_from.name, self.name))
            self._write(addr, dirty=False)
            return True

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
                #chech that first element is invalid
                if candidate_set[0].valid:
                    raise Exception("ERROR")
                candidate_set[0] = CacheLine(addr, self.get_tag(addr), valid=True, dirty=dirty)
        

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
        
    def allocate_for(self, addr):
        #can return an invalid line!! be careful
        if addr in self:
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
                linestr.append(line.prettyprint(self.address_width - self.line_size_width - self.set_width))

            setstr.append(",".join(linestr) + " " + prettydir(i << self.line_size_width, self.line_size_width + self.set_width, self.set_width, self.line_size_width))
                        
        if self.victim:
            return "\n".join(setstr) + "\n" + str(self.victim)
        else:
            return "\n".join(setstr)





def main():
    line_size_width = 4
    address_width = 16
    set_width = 2 # 4 sets
    way_width = 1 # 2 ways

    mem = MainMemory(address_width = address_width, line_size_width = line_size_width)
    victim = Cache("L1-Victim", 0, 1, line_size_width = line_size_width, replacement_policy = ReplacementPolicy.LRU, address_width = address_width)
    cache = Cache("L1", set_width, way_width, line_size_width = line_size_width, replacement_policy = ReplacementPolicy.LRU, load_from = mem, store_to = mem, victim = victim, address_width = address_width)

    cache.read(0x2001)
    cache.read(0x2002)
    cache.write(0x2003)
    cache.write(0x2003)
    cache.write(0x3003)
    cache.write(0x4003)
    cache.write(0x5003)
    cache.write(0x6003)
    cache.read(0x4003)

    print(cache)



main()