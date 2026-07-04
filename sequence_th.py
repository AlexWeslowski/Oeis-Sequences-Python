import subprocess
import sys
import re
import os
import warnings
import packaging
import packaging.version
import importlib
import importlib.metadata

"""
class Packages:
	def __init__(self):		
		self.exclude = sys.stdlib_module_names
		self.package_list = {'numpy', 'primefac', 'cpuinfo', 'divisors', 'sympy', 'numba', 'bitarray', 'filelock', 'sparse', 'psutil', 'packaging', 'platformdirs'}
		self.requirements = {}
		self.requirements["bitarray"] = packaging.version.Version("3.8.2")
		self.requirements["divisors"] = packaging.version.Version("1.1.9")
		self.requirements["numba"] = packaging.version.Version("0.66.0")
		self.requirements["numpy"] = packaging.version.Version("2.4.6")
		self.package_hash = {}
		self.package_hash["cpuinfo"] = "py-cpuinfo"
"""

class Packages:
	def __init__(self):		
		#self.exclude = ["math", "multiprocessing", "fractions", "os", "time", "numbers", "itertools", "traceback", "queue", "cpuinfo", "sqlite3", "sys", "threading", "random", "subprocess", "io", "signal", "operator", "warnings", "gzip", "re"]
		self.exclude = sys.stdlib_module_names
		self.package_list = set()
		#print(os.path.abspath(__file__))
		with warnings.catch_warnings():
			warnings.filterwarnings("error", category=SyntaxWarning)
			#filepath = os.path.join(directory, "sequence_th.py")
			filepath = os.path.abspath(__file__)
			with open(filepath, 'r', encoding='utf8') as f:
				try:
					block_comment = False
					for line in f:
						if line.startswith("\"\"\""):
							block_comment = not block_comment
						if not line.startswith("#") and not block_comment:
							if line.startswith("import "):
								self.add(line[7:])
							elif line.startswith("from "):
								self.add(line[5:])
				except SyntaxWarning as sw:
					pass
		self.requirements = {}
		self.read_requirements()
		self.package_hash = {}
		self.package_hash["cpuinfo"] = "py-cpuinfo"
		
	def add(self, module):
		if module.find(",") > 0:
			for m in module.split(","):
				if m not in self.exclude:
					self.add(m)
			return
		if module.find(".") > 0:
			module = module.split(".")[0].strip()
		elif module.find(" as ") > 0:
			module = module.split(" as ")[0].strip()
		elif module.find(" import ") > 0:
			module = module.split(" import ")[0].strip()
		else:
			module = module.strip()
		if module not in self.exclude:
			self.package_list.add(module)

	def append(self, package_name):
		self.add(package_name)
	
	def map(self, package_name, dist_name):
		self.package_hash[package_name] = dist_name
	
	def read_requirements(self, directory=None):
		if not directory:
			directory = os.path.dirname(os.path.abspath(__file__))
		with open(os.path.join(directory, "requirements.txt")) as f:
			for line in f:
				if len(line) > 1:
					#numpy==2.4.6
					#divisors==1.1.9 @ git+https://github.com/AlexWeslowski/Divisors.git
					ary = line.strip().split("==")
					at = ary[1].find("@")
					if at > 0:
						ary[1] = ary[1][:at].strip()
					self.requirements[ary[0]] = packaging.version.Version(ary[1])
	
	def write_requirements(self, directory=None):
		if not directory:
			directory = os.path.dirname(os.path.abspath(__file__))
		inpath = os.path.join(directory, "requirements.in")
		outpath = os.path.join(directory, "requirements.txt")
		with open(inpath, "w") as f:
			f.writelines(pkg + "\n" for pkg in self.package_list if pkg not in exclude)
		process = subprocess.run(["python", "-m", "piptools", "compile", inpath, "-o", outpath], check=True)
		print(process.stdout)
		with open(outpath, "r") as f:
			lines = f.readlines()
		clean = [line for line in lines if not line.strip().startswith("#") and line.strip()]
		with open(outpath, "w") as f:
			f.writelines(line.rstrip() + "\n" for line in clean)
	
	def pip_install(self, package_name, binstall, bupgrade):
		bsuccess = False
		try:
			install_name = package_name
			if install_name in self.package_hash:
				install_name = self.package_hash[install_name]
			if binstall:
				process = subprocess.run([sys.executable, "-m", "pip", "install", install_name], check=True, capture_output=True, text=True)
			elif bupgrade:
				process = subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "--pre",  install_name], check=True, capture_output=True, text=True)
			print(process.stdout)
			#if not is_git:
			_ = __import__(package_name)
			bsuccess = True
		except (ModuleNotFoundError, ImportError) as ex:
			print(f"pip_install(package_name={package_name}, binstall={binstall}, bupgrade={bupgrade}) {ex}")
			bpass = False
			if binstall:
				if self.pip_install(package_name, False, True):
					bsuccess = True
					bpass = True
			if bpass:
				pass
			else:
				print(ex)
		except subprocess.CalledProcessError as cpe:
			print(f"Exit Code: {cpe.returncode}")
			print("[STDOUT]")
			print(cpe.stdout) 
			print("[STDERR]")
			print(cpe.stderr) 
			pass
		except FileNotFoundError as fnfe:
			print("\nError: pip command or python executable was not found.")
			pass
		return bsuccess
	
	def install(self):
		print("")
		print("Checking installed packages")
		print(self.package_list)
		print("")
		for package_name in self.package_list:
			if package_name in self.exclude:
				continue
			binstall = False
			bupgrade = False
			try:
				#is_git = package_name.startswith("git+") or package_name.find("https://") > 0
				if False:
					spec = importlib.util.find_spec(package_name)
					if spec is None:
						raise ImportError(f"Package installed but module '{package_name}' is not found.")
				#if not is_git:
				module = __import__(package_name)
				sversion = getattr(module, "__version__", None)
				if not sversion:
					try:
						sversion = importlib.metadata.version(package_name)
					except importlib.metadata.PackageNotFoundError as pnfe:
						if package_name in self.package_hash:
							sversion = importlib.metadata.version(self.package_hash[package_name])
							pass
				rc = sversion.find("rc")
				if rc > 0:
					sversion = sversion[:rc]
				oversion = packaging.version.Version(sversion)
				if False and package_name in self.requirements:
					print(f"install(package_name={package_name}) version = {oversion}")
					print(f"install(package_name={package_name}) requirement = {self.requirements[package_name]}")
				if package_name in self.requirements and oversion < self.requirements[package_name]:
					bupgrade = True
				#eval(f"{package_name} = __import__('{package_name}')")
			except (ModuleNotFoundError, ImportError) as ex:
				print(f"install(package_name={package_name}) {ex}")
				binstall = True
				pass
			if binstall or bupgrade:
				self.pip_install(package_name, binstall, bupgrade)


#import sys
#directory = r"D:\Python\Sequence"
#directory = r"H:\Python\Sequence"
#directory = r"C:\Users\alex.weslowski\Documents\Python\Sequence"
#sys.path.append(directory)
#import sequence_th
#p = sequence_th.Packages()
#p.write_requirements(directory)

#pip-compile requirements.in --output-file requirements.txt
#python3.14t.exe -m pip install packaging --upgrade --pre
#python3.14t.exe -m pip install H:\C++\AlexWeslowski\Divisors
#divisors==1.1.9 @ git+https://github.com/AlexWeslowski/Divisors.git

p = Packages()
#package_list = "multiprocessing, math, numpy, numba, sympy, sparse, itertools, functools, operator, primefac, bitarray, numbers, operator, fractions, random, sqlite3, filelock, io, gzip, threading, queue, traceback, signal, time, psutil, os, pathlib, platformdirs, traceback, datetime, py-cpuinfo".split(", ")
#p.add("git+https://github.com/AlexWeslowski/Divisors.git")
p.map("divisors", "git+https://github.com/AlexWeslowski/Divisors.git")
p.install()
#print(f"package_list, len = {len(p.package_list)}")
#print(p.package_list)


import multiprocessing, math, numpy, sparse, itertools, functools, operator, primefac, bitarray, numbers, operator, fractions, random, sqlite3, filelock, io, gzip, threading, queue, traceback, signal, time, psutil, os, pathlib, platformdirs, traceback, datetime, cpuinfo
import numba, numba.experimental, numba.extending, numba.typed, numba.types
import sympy, sympy.external.gmpy
from multiprocessing import Process
import divisors

MAX_RECURSION = 8
bln_cpp = True
bln_numba = True
bln_divisors = True
save_memory = False
verbose = False

ap = 2**10

def fill_primes(ap1):
	global verbose
	global bln_cpp
	global bln_numba
	ary = None
	t0 = time.time()
	log2 = math.log(ap1, 2)
	ap2 = 2**math.ceil(log2) + 2**math.floor(log2)
	# [i for i in range(2**27, 2**27 - 512, -1) if len(divisors.divisors(i)) > 128]
	# 2**26 ... 67,108,862
	# 2**27 ... 134,217,600 ...  12.83 seconds
	# 2**28 ... 268,435,116 ... 
	# 2**29 ... 536,870,917 ... 125.88 seconds
	thresh = 2**27
	name = "sequence_th "
	name = ""
	if verbose: print(f"{name}fill_primes({ap1:,})")
	if ap2 > thresh:
		sys.stdout.write(f"{name}fill_primes({ap1:,}) at 0.0%")
		sys.stdout.flush()
	if bln_numba and not bln_cpp:
		ary = numpy.array([False]*(ap2+2), dtype=bool)
	else:
		ary = bitarray.bitarray(ap2+2)
		#ary.setall(0)
	
	spinner = ["|", "/", "-", "\\"]
	i, j, ilen, prevpct, thispct = 1, -1, len(spinner), -0.1, 0.0
	def spin(p):
		nonlocal i, j, prevpct, thispct
		if ap2 <= thresh:
			return
		i += 1
		if i % 10000 == 0:
			thispct = round(100.0 * p / ap2, 1)
			if thispct >= 99.9:
				thispct = 100.0
			if thispct > prevpct:
				j += 1
				sys.stdout.write(f"\r{name}fill_primes({ap1:,}) at {thispct:.1f}% {spinner[j % ilen]}")
				sys.stdout.flush()
				prevpct = thispct
	
	try:
		import primesieve
		for p in primesieve.primes(ap2+1):
			ary[p] = True
			spin(p)
	except (ModuleNotFoundError, ImportError) as ex:
		if False:
			for p in sympy.sieve.primerange(ap2+1):
				ary[p] = True
				spin(p)
		if True:
			for p in divisors.primerange(2, ap2+1):
				ary[p] = True
				spin(p)
		pass
	if ap2 > thresh: 
		sys.stdout.write(f"\r{name}fill_primes({ap1:,}) at 100.0%")
		sys.stdout.flush()
		print()
	if verbose: 
		print(f"{name}fill_primes({ap1:,}) len(ary) = {len(ary)}")
		dt = time.time() - t0
		print(f"{name}fill_primes() {round(dt, 2):.2f} seconds elapsed")
	return ary

# 2**28 ~ 10**8.43
# 2**33 ~ 10**9.93
aryprimes = fill_primes(ap)

def size():
	global aryprimes
	return len(aryprimes)

def test_primes():
	global aryprimes
	ilen = len(aryprimes)
	test = [random.randint(2, ilen) for _ in range(2**22)]
	t0ary = time.time()
	for t in test:
		is_prime = aryprimes[t]
	dtary = time.time() - t0ary
	t0div = time.time()
	for t in test:
		is_prime = divisors.is_prime(t)
	dtdiv = time.time() - t0div
	#aryprimes ... 0.36
	#divisors .... 2.24
	print(f"aryprimes elapsed = {round(dtary, 2):.2f}")
	print(f"divisors.is_prime elapsed = {round(dtdiv, 2):.2f}")

spec = [
	('numerator', numba.types.int64),
	('denominator', numba.types.int64),
]

@numba.experimental.jitclass(spec)
class Fraction():
	#__slots__ = ('numerator', 'denominator')
	
	def __init__(self, num, den):
		if num == 1:
			self.numerator = num
			self.denominator = den
		else:
			g = numpy.gcd(num, den)
			if den < 0:
				g = -g
			self.numerator = num//g
			self.denominator = den//g
	
	def __add__(self, b):
		na, da = self.numerator, self.denominator
		nb, db = b.numerator, b.denominator
		g1 = numpy.gcd(da, db)
		if g1 == 1:
			return Fraction(na * db + da * nb, da * db)
		s = da // g1
		t = na * (db // g1) + nb * s
		g2 = numpy.gcd(t, g1)
		if g2 == 1:
			return Fraction(t, s * db)
		return Fraction(t // g2, s * (db // g2))

	#__add__, __radd__ = _operator_fallbacks(_add, operator.add)

	def __sub__(self, b):
		na, da = self.numerator, self.denominator
		nb, db = b.numerator, b.denominator
		g1 = numpy.gcd(da, db)
		if g1 == 1:
			return Fraction(na * db - da * nb, da * db)
		s = da // g1
		t = na * (db // g1) - nb * s
		g2 = numpy.gcd(t, g1)
		if g2 == 1:
			return Fraction(t, s * db)
		return Fraction(t // g2, s * (db // g2))

	#__sub__, __rsub__ = _operator_fallbacks(_sub, operator.sub)
	
	def __mul__(self, b):
		na, da = self.numerator, self.denominator
		nb, db = b.numerator, b.denominator
		g1 = numpy.gcd(na, db)
		if g1 > 1:
			na //= g1
			db //= g1
		g2 = numpy.gcd(nb, da)
		if g2 > 1:
			nb //= g2
			da //= g2
		return Fraction(na * nb, db * da)

	def __str__(self):
		if self.denominator == 1:
			return str(self.numerator)
		else:
			#return '%s/%s' % (self.numerator, self.denominator)
			return str(self.numerator) + "/" + str(self.denominator)
	
	def __lt__(a, b):
		return a.numerator * b.denominator < a.denominator * b.numerator

	def __gt__(a, b):
		return a.numerator * b.denominator > a.denominator * b.numerator

	def __le__(a, b):
		return a.numerator * b.denominator <= a.denominator * b.numerator

	def __ge__(a, b):
		return a.numerator * b.denominator >= a.denominator * b.numerator
	
	def __eq__(a, b):
		return a.numerator == b.numerator and a.denominator == b.denominator
	
	def __hash__(self):
		return hash((self.numerator, self.denominator))




@numba.jit(nopython=True)
def mult_numba(tpl):
	global bln_cpp
	global bln_numba
	global aryprimes
	if bln_cpp:
		print("Error in mult_numba(), bln_cpp is True")
	ary = list(tpl)
	ilen = len(ary)	
	if ilen <= 2:
		# ary[1] = ary[0]*ary[1] if aryprimes[ary[0]] or aryprimes[ary[1]] else ary[0]*ary[1]//numpy.gcd(ary[0], ary[1])
		ary[1] = ary[0]*ary[1] if aryprimes[ary[0]] or aryprimes[ary[1]] else numpy.lcm(ary[0], ary[1])
		return ary[1]
	else:
		# ary[1] = ary[0]*ary[1] if aryprimes[ary[0]] or aryprimes[ary[1]] else ary[0]*ary[1]//numpy.gcd(ary[0], ary[1])
		ary[1] = ary[0]*ary[1] if aryprimes[ary[0]] or aryprimes[ary[1]] else numpy.lcm(ary[0], ary[1])
		for a in range(2, ilen):
			# ary[a] = ary[a-1]*ary[a] if aryprimes[ary[a]] else ary[a-1]*ary[a]//numpy.gcd(ary[a-1], ary[a])
			ary[a] = ary[a-1]*ary[a] if aryprimes[ary[a]] else numpy.lcm(ary[a-1], ary[a])
			if ilen <= a + 1:
				return ary[a]

def mult(tpl):
	global bln_cpp
	global bln_numba
	global aryprimes
	if bln_cpp:
		print("Error in mult(), bln_cpp is True")
	ary = list(tpl)
	ilen = len(ary)	
	if ilen <= 2:
		# ary[1] = ary[0]*ary[1] if aryprimes[ary[0]] or aryprimes[ary[1]] else ary[0]*ary[1]//numpy.gcd(ary[0], ary[1])
		ary[1] = ary[0]*ary[1] if aryprimes[ary[0]] or aryprimes[ary[1]] else numpy.lcm(ary[0], ary[1])
		return ary[1]
	else:
		# ary[1] = ary[0]*ary[1] if aryprimes[ary[0]] or aryprimes[ary[1]] else ary[0]*ary[1]//numpy.gcd(ary[0], ary[1])
		ary[1] = ary[0]*ary[1] if aryprimes[ary[0]] or aryprimes[ary[1]] else numpy.lcm(ary[0], ary[1])
		for a in range(2, ilen):
			# ary[a] = ary[a-1]*ary[a] if aryprimes[ary[a]] else ary[a-1]*ary[a]//numpy.gcd(ary[a-1], ary[a])
			ary[a] = ary[a-1]*ary[a] if aryprimes[ary[a]] else numpy.lcm(ary[a-1], ary[a])
			if ilen <= a + 1:
				return ary[a]


bcheckprime = False
max_sum = divisors.BoostRational(1, 1) if bln_cpp else Fraction(1, 1) if bln_numba else fractions.Fraction(1, 1)
setfractions = frozenset([divisors.BoostRational(1, 2) if bln_cpp else Fraction(1, 2) if bln_numba else fractions.Fraction(1, 2),])
min_factors = 2
max_factors = 10
max_denominator = 3

#factorizations_outer(720)
#calc_density2(720, [5, 9, 16], max_sum)
@numba.jit(nopython=True)
def calc_density_numba(i, a, max_sum):
	#print(f"calc_density_numba({i}, {a}, {max_sum})")
	#global bcheckprime
	#global aryprimes
	bcheckmax = False
	ilen = len(a)
	frac = Fraction(1, a[0])
	if frac > max_sum:
		return Fraction(1, 1)
	frac += Fraction(1, a[1]) - Fraction(1, mult_numba(a[0:2]))
	if bcheckmax and frac > max_sum:
		return Fraction(1, 1)
	if ilen >= 3:
		frac += Fraction(1, a[2]) - Fraction(1, mult_numba((a[0], a[2]))) - Fraction(1, mult_numba((a[1], a[2]))) + Fraction(1, mult_numba(a[0:3]))
		if bcheckmax and frac > max_sum:
			return Fraction(1, 1)
	if ilen >= 4:
		frac += Fraction(1, a[3]) - Fraction(1, mult_numba((a[0], a[3]))) - Fraction(1, mult_numba((a[1], a[3]))) - Fraction(1, mult_numba((a[2], a[3]))) + Fraction(1, mult_numba((a[0], a[1], a[3]))) + Fraction(1, mult_numba((a[0], a[2], a[3]))) + Fraction(1, mult_numba((a[1], a[2], a[3]))) - Fraction(1, mult_numba(a[0:4]))
		if bcheckmax and frac > max_sum:
			return Fraction(1, 1)
	if ilen >= 5:
		frac += Fraction(1, a[4]) - Fraction(1, mult_numba((a[0], a[4]))) - Fraction(1, mult_numba((a[1], a[4]))) - Fraction(1, mult_numba((a[2], a[4]))) - Fraction(1, mult_numba((a[3], a[4]))) + Fraction(1, mult_numba((a[0], a[1], a[4]))) + Fraction(1, mult_numba((a[0], a[2], a[4]))) + Fraction(1, mult_numba((a[0], a[3], a[4]))) + Fraction(1, mult_numba((a[1], a[2], a[4]))) + Fraction(1, mult_numba((a[1], a[3], a[4]))) + Fraction(1, mult_numba((a[2], a[3], a[4]))) - Fraction(1, mult_numba((a[0], a[1], a[2], a[4]))) - Fraction(1, mult_numba((a[0], a[1], a[3], a[4]))) - Fraction(1, mult_numba((a[0], a[2], a[3], a[4]))) - Fraction(1, mult_numba((a[1], a[2], a[3], a[4]))) + Fraction(1, mult_numba(a[0:5]))
		if bcheckmax and frac > max_sum:
			return Fraction(1, 1)
	if ilen >= 6:
		frac += Fraction(1, a[5]) - Fraction(1, mult_numba((a[0], a[5]))) - Fraction(1, mult_numba((a[1], a[5]))) - Fraction(1, mult_numba((a[2], a[5]))) - Fraction(1, mult_numba((a[3], a[5]))) - Fraction(1, mult_numba((a[4], a[5]))) + Fraction(1, mult_numba((a[0], a[1], a[5]))) + Fraction(1, mult_numba((a[0], a[2], a[5]))) + Fraction(1, mult_numba((a[0], a[3], a[5]))) + Fraction(1, mult_numba((a[0], a[4], a[5]))) + Fraction(1, mult_numba((a[1], a[2], a[5]))) + Fraction(1, mult_numba((a[1], a[3], a[5]))) + Fraction(1, mult_numba((a[1], a[4], a[5]))) + Fraction(1, mult_numba((a[2], a[3], a[5]))) + Fraction(1, mult_numba((a[2], a[4], a[5]))) + Fraction(1, mult_numba((a[3], a[4], a[5]))) - Fraction(1, mult_numba((a[0], a[1], a[2], a[5]))) - Fraction(1, mult_numba((a[0], a[1], a[3], a[5]))) - Fraction(1, mult_numba((a[0], a[1], a[4], a[5]))) - Fraction(1, mult_numba((a[0], a[2], a[3], a[5]))) - Fraction(1, mult_numba((a[0], a[2], a[4], a[5]))) - Fraction(1, mult_numba((a[0], a[3], a[4], a[5]))) - Fraction(1, mult_numba((a[1], a[2], a[3], a[5]))) - Fraction(1, mult_numba((a[1], a[2], a[4], a[5]))) - Fraction(1, mult_numba((a[1], a[3], a[4], a[5]))) - Fraction(1, mult_numba((a[2], a[3], a[4], a[5]))) + Fraction(1, mult_numba((a[0], a[1], a[2], a[3], a[5]))) + Fraction(1, mult_numba((a[0], a[1], a[2], a[4], a[5]))) + Fraction(1, mult_numba((a[0], a[1], a[3], a[4], a[5]))) + Fraction(1, mult_numba((a[0], a[2], a[3], a[4], a[5]))) + Fraction(1, mult_numba((a[1], a[2], a[3], a[4], a[5]))) - Fraction(1, mult_numba(a[0:6]))
		if bcheckmax and frac > max_sum:
			return Fraction(1, 1)
	if ilen >= 7:
		frac += Fraction(1, a[6]) - Fraction(1, mult_numba((a[0], a[6]))) - Fraction(1, mult_numba((a[1], a[6]))) - Fraction(1, mult_numba((a[2], a[6]))) - Fraction(1, mult_numba((a[3], a[6]))) - Fraction(1, mult_numba((a[4], a[6]))) - Fraction(1, mult_numba((a[5], a[6]))) + Fraction(1, mult_numba((a[0], a[1], a[6]))) + Fraction(1, mult_numba((a[0], a[2], a[6]))) + Fraction(1, mult_numba((a[0], a[3], a[6]))) + Fraction(1, mult_numba((a[0], a[4], a[6]))) + Fraction(1, mult_numba((a[0], a[5], a[6]))) + Fraction(1, mult_numba((a[1], a[2], a[6]))) + Fraction(1, mult_numba((a[1], a[3], a[6]))) + Fraction(1, mult_numba((a[1], a[4], a[6]))) + Fraction(1, mult_numba((a[1], a[5], a[6]))) + Fraction(1, mult_numba((a[2], a[3], a[6]))) + Fraction(1, mult_numba((a[2], a[4], a[6]))) + Fraction(1, mult_numba((a[2], a[5], a[6]))) + Fraction(1, mult_numba((a[3], a[4], a[6]))) + Fraction(1, mult_numba((a[3], a[5], a[6]))) + Fraction(1, mult_numba((a[4], a[5], a[6]))) - Fraction(1, mult_numba((a[0], a[1], a[2], a[6]))) - Fraction(1, mult_numba((a[0], a[1], a[3], a[6]))) - Fraction(1, mult_numba((a[0], a[1], a[4], a[6]))) - Fraction(1, mult_numba((a[0], a[1], a[5], a[6]))) - Fraction(1, mult_numba((a[0], a[2], a[3], a[6]))) - Fraction(1, mult_numba((a[0], a[2], a[4], a[6]))) - Fraction(1, mult_numba((a[0], a[2], a[5], a[6]))) - Fraction(1, mult_numba((a[0], a[3], a[4], a[6]))) - Fraction(1, mult_numba((a[0], a[3], a[5], a[6]))) - Fraction(1, mult_numba((a[0], a[4], a[5], a[6]))) - Fraction(1, mult_numba((a[1], a[2], a[3], a[6]))) - Fraction(1, mult_numba((a[1], a[2], a[4], a[6]))) - Fraction(1, mult_numba((a[1], a[2], a[5], a[6]))) - Fraction(1, mult_numba((a[1], a[3], a[4], a[6]))) - Fraction(1, mult_numba((a[1], a[3], a[5], a[6]))) - Fraction(1, mult_numba((a[1], a[4], a[5], a[6]))) - Fraction(1, mult_numba((a[2], a[3], a[4], a[6]))) - Fraction(1, mult_numba((a[2], a[3], a[5], a[6]))) - Fraction(1, mult_numba((a[2], a[4], a[5], a[6]))) - Fraction(1, mult_numba((a[3], a[4], a[5], a[6]))) + Fraction(1, mult_numba((a[0], a[1], a[2], a[3], a[6]))) + Fraction(1, mult_numba((a[0], a[1], a[2], a[4], a[6]))) + Fraction(1, mult_numba((a[0], a[1], a[2], a[5], a[6]))) + Fraction(1, mult_numba((a[0], a[1], a[3], a[4], a[6]))) + Fraction(1, mult_numba((a[0], a[1], a[3], a[5], a[6]))) + Fraction(1, mult_numba((a[0], a[1], a[4], a[5], a[6]))) + Fraction(1, mult_numba((a[0], a[2], a[3], a[4], a[6]))) + Fraction(1, mult_numba((a[0], a[2], a[3], a[5], a[6]))) + Fraction(1, mult_numba((a[0], a[2], a[4], a[5], a[6]))) + Fraction(1, mult_numba((a[0], a[3], a[4], a[5], a[6]))) + Fraction(1, mult_numba((a[1], a[2], a[3], a[4], a[6]))) + Fraction(1, mult_numba((a[1], a[2], a[3], a[5], a[6]))) + Fraction(1, mult_numba((a[1], a[2], a[4], a[5], a[6]))) + Fraction(1, mult_numba((a[1], a[3], a[4], a[5], a[6]))) + Fraction(1, mult_numba((a[2], a[3], a[4], a[5], a[6]))) - Fraction(1, mult_numba((a[0], a[1], a[2], a[3], a[4], a[6]))) - Fraction(1, mult_numba((a[0], a[1], a[2], a[3], a[5], a[6]))) - Fraction(1, mult_numba((a[0], a[1], a[2], a[4], a[5], a[6]))) - Fraction(1, mult_numba((a[0], a[1], a[3], a[4], a[5], a[6]))) - Fraction(1, mult_numba((a[0], a[2], a[3], a[4], a[5], a[6]))) - Fraction(1, mult_numba((a[1], a[2], a[3], a[4], a[5], a[6]))) + Fraction(1, mult_numba(a[0:7]))
		if bcheckmax and frac > max_sum:
			return Fraction(1, 1)
	if ilen >= 8:
		frac += Fraction(1, a[7]) - Fraction(1, mult_numba((a[0], a[7]))) - Fraction(1, mult_numba((a[1], a[7]))) - Fraction(1, mult_numba((a[2], a[7]))) - Fraction(1, mult_numba((a[3], a[7]))) - Fraction(1, mult_numba((a[4], a[7]))) - Fraction(1, mult_numba((a[5], a[7]))) - Fraction(1, mult_numba((a[6], a[7]))) + Fraction(1, mult_numba((a[0], a[1], a[7]))) + Fraction(1, mult_numba((a[0], a[2], a[7]))) + Fraction(1, mult_numba((a[0], a[3], a[7]))) + Fraction(1, mult_numba((a[0], a[4], a[7]))) + Fraction(1, mult_numba((a[0], a[5], a[7]))) + Fraction(1, mult_numba((a[0], a[6], a[7]))) + Fraction(1, mult_numba((a[1], a[2], a[7]))) + Fraction(1, mult_numba((a[1], a[3], a[7]))) + Fraction(1, mult_numba((a[1], a[4], a[7]))) + Fraction(1, mult_numba((a[1], a[5], a[7]))) + Fraction(1, mult_numba((a[1], a[6], a[7]))) + Fraction(1, mult_numba((a[2], a[3], a[7]))) + Fraction(1, mult_numba((a[2], a[4], a[7]))) + Fraction(1, mult_numba((a[2], a[5], a[7]))) + Fraction(1, mult_numba((a[2], a[6], a[7]))) + Fraction(1, mult_numba((a[3], a[4], a[7]))) + Fraction(1, mult_numba((a[3], a[5], a[7]))) + Fraction(1, mult_numba((a[3], a[6], a[7]))) + Fraction(1, mult_numba((a[4], a[5], a[7]))) + Fraction(1, mult_numba((a[4], a[6], a[7]))) + Fraction(1, mult_numba((a[5], a[6], a[7]))) - Fraction(1, mult_numba((a[0], a[1], a[2], a[7]))) - Fraction(1, mult_numba((a[0], a[1], a[3], a[7]))) - Fraction(1, mult_numba((a[0], a[1], a[4], a[7]))) - Fraction(1, mult_numba((a[0], a[1], a[5], a[7]))) - Fraction(1, mult_numba((a[0], a[1], a[6], a[7]))) - Fraction(1, mult_numba((a[0], a[2], a[3], a[7]))) - Fraction(1, mult_numba((a[0], a[2], a[4], a[7]))) - Fraction(1, mult_numba((a[0], a[2], a[5], a[7]))) - Fraction(1, mult_numba((a[0], a[2], a[6], a[7]))) - Fraction(1, mult_numba((a[0], a[3], a[4], a[7]))) - Fraction(1, mult_numba((a[0], a[3], a[5], a[7]))) - Fraction(1, mult_numba((a[0], a[3], a[6], a[7]))) - Fraction(1, mult_numba((a[0], a[4], a[5], a[7]))) - Fraction(1, mult_numba((a[0], a[4], a[6], a[7]))) - Fraction(1, mult_numba((a[0], a[5], a[6], a[7]))) - Fraction(1, mult_numba((a[1], a[2], a[3], a[7]))) - Fraction(1, mult_numba((a[1], a[2], a[4], a[7]))) - Fraction(1, mult_numba((a[1], a[2], a[5], a[7]))) - Fraction(1, mult_numba((a[1], a[2], a[6], a[7]))) - Fraction(1, mult_numba((a[1], a[3], a[4], a[7]))) - Fraction(1, mult_numba((a[1], a[3], a[5], a[7]))) - Fraction(1, mult_numba((a[1], a[3], a[6], a[7]))) - Fraction(1, mult_numba((a[1], a[4], a[5], a[7]))) - Fraction(1, mult_numba((a[1], a[4], a[6], a[7]))) - Fraction(1, mult_numba((a[1], a[5], a[6], a[7]))) - Fraction(1, mult_numba((a[2], a[3], a[4], a[7]))) - Fraction(1, mult_numba((a[2], a[3], a[5], a[7]))) - Fraction(1, mult_numba((a[2], a[3], a[6], a[7]))) - Fraction(1, mult_numba((a[2], a[4], a[5], a[7]))) - Fraction(1, mult_numba((a[2], a[4], a[6], a[7]))) - Fraction(1, mult_numba((a[2], a[5], a[6], a[7]))) - Fraction(1, mult_numba((a[3], a[4], a[5], a[7]))) - Fraction(1, mult_numba((a[3], a[4], a[6], a[7]))) - Fraction(1, mult_numba((a[3], a[5], a[6], a[7]))) - Fraction(1, mult_numba((a[4], a[5], a[6], a[7]))) + Fraction(1, mult_numba((a[0], a[1], a[2], a[3], a[7]))) + Fraction(1, mult_numba((a[0], a[1], a[2], a[4], a[7]))) + Fraction(1, mult_numba((a[0], a[1], a[2], a[5], a[7]))) + Fraction(1, mult_numba((a[0], a[1], a[2], a[6], a[7]))) + Fraction(1, mult_numba((a[0], a[1], a[3], a[4], a[7]))) + Fraction(1, mult_numba((a[0], a[1], a[3], a[5], a[7]))) + Fraction(1, mult_numba((a[0], a[1], a[3], a[6], a[7]))) + Fraction(1, mult_numba((a[0], a[1], a[4], a[5], a[7])))
		frac += Fraction(1, mult_numba((a[0], a[1], a[4], a[6], a[7]))) + Fraction(1, mult_numba((a[0], a[1], a[5], a[6], a[7]))) + Fraction(1, mult_numba((a[0], a[2], a[3], a[4], a[7]))) + Fraction(1, mult_numba((a[0], a[2], a[3], a[5], a[7]))) + Fraction(1, mult_numba((a[0], a[2], a[3], a[6], a[7]))) + Fraction(1, mult_numba((a[0], a[2], a[4], a[5], a[7]))) + Fraction(1, mult_numba((a[0], a[2], a[4], a[6], a[7]))) + Fraction(1, mult_numba((a[0], a[2], a[5], a[6], a[7]))) + Fraction(1, mult_numba((a[0], a[3], a[4], a[5], a[7]))) + Fraction(1, mult_numba((a[0], a[3], a[4], a[6], a[7]))) + Fraction(1, mult_numba((a[0], a[3], a[5], a[6], a[7]))) + Fraction(1, mult_numba((a[0], a[4], a[5], a[6], a[7]))) + Fraction(1, mult_numba((a[1], a[2], a[3], a[4], a[7]))) + Fraction(1, mult_numba((a[1], a[2], a[3], a[5], a[7]))) + Fraction(1, mult_numba((a[1], a[2], a[3], a[6], a[7]))) + Fraction(1, mult_numba((a[1], a[2], a[4], a[5], a[7]))) + Fraction(1, mult_numba((a[1], a[2], a[4], a[6], a[7]))) + Fraction(1, mult_numba((a[1], a[2], a[5], a[6], a[7]))) + Fraction(1, mult_numba((a[1], a[3], a[4], a[5], a[7]))) + Fraction(1, mult_numba((a[1], a[3], a[4], a[6], a[7]))) + Fraction(1, mult_numba((a[1], a[3], a[5], a[6], a[7]))) + Fraction(1, mult_numba((a[1], a[4], a[5], a[6], a[7]))) + Fraction(1, mult_numba((a[2], a[3], a[4], a[5], a[7]))) + Fraction(1, mult_numba((a[2], a[3], a[4], a[6], a[7]))) + Fraction(1, mult_numba((a[2], a[3], a[5], a[6], a[7]))) + Fraction(1, mult_numba((a[2], a[4], a[5], a[6], a[7]))) + Fraction(1, mult_numba((a[3], a[4], a[5], a[6], a[7]))) - Fraction(1, mult_numba((a[0], a[1], a[2], a[3], a[4], a[7]))) - Fraction(1, mult_numba((a[0], a[1], a[2], a[3], a[5], a[7]))) - Fraction(1, mult_numba((a[0], a[1], a[2], a[3], a[6], a[7]))) - Fraction(1, mult_numba((a[0], a[1], a[2], a[4], a[5], a[7]))) - Fraction(1, mult_numba((a[0], a[1], a[2], a[4], a[6], a[7]))) - Fraction(1, mult_numba((a[0], a[1], a[2], a[5], a[6], a[7]))) - Fraction(1, mult_numba((a[0], a[1], a[3], a[4], a[5], a[7]))) - Fraction(1, mult_numba((a[0], a[1], a[3], a[4], a[6], a[7]))) - Fraction(1, mult_numba((a[0], a[1], a[3], a[5], a[6], a[7]))) - Fraction(1, mult_numba((a[0], a[1], a[4], a[5], a[6], a[7]))) - Fraction(1, mult_numba((a[0], a[2], a[3], a[4], a[5], a[7]))) - Fraction(1, mult_numba((a[0], a[2], a[3], a[4], a[6], a[7]))) - Fraction(1, mult_numba((a[0], a[2], a[3], a[5], a[6], a[7]))) - Fraction(1, mult_numba((a[0], a[2], a[4], a[5], a[6], a[7]))) - Fraction(1, mult_numba((a[0], a[3], a[4], a[5], a[6], a[7]))) - Fraction(1, mult_numba((a[1], a[2], a[3], a[4], a[5], a[7]))) - Fraction(1, mult_numba((a[1], a[2], a[3], a[4], a[6], a[7]))) - Fraction(1, mult_numba((a[1], a[2], a[3], a[5], a[6], a[7]))) - Fraction(1, mult_numba((a[1], a[2], a[4], a[5], a[6], a[7]))) - Fraction(1, mult_numba((a[1], a[3], a[4], a[5], a[6], a[7]))) - Fraction(1, mult_numba((a[2], a[3], a[4], a[5], a[6], a[7]))) + Fraction(1, mult_numba((a[0], a[1], a[2], a[3], a[4], a[5], a[7]))) + Fraction(1, mult_numba((a[0], a[1], a[2], a[3], a[4], a[6], a[7]))) + Fraction(1, mult_numba((a[0], a[1], a[2], a[3], a[5], a[6], a[7]))) + Fraction(1, mult_numba((a[0], a[1], a[2], a[4], a[5], a[6], a[7]))) + Fraction(1, mult_numba((a[0], a[1], a[3], a[4], a[5], a[6], a[7]))) + Fraction(1, mult_numba((a[0], a[2], a[3], a[4], a[5], a[6], a[7]))) + Fraction(1, mult_numba((a[1], a[2], a[3], a[4], a[5], a[6], a[7]))) - Fraction(1, mult_numba(a[0:8]))
		if bcheckmax and frac > max_sum:
			return Fraction(1, 1)
	if ilen >= 9:
		frac += Fraction(1, a[8]) - Fraction(1, mult_numba((a[0], a[8]))) - Fraction(1, mult_numba((a[1], a[8]))) - Fraction(1, mult_numba((a[2], a[8]))) - Fraction(1, mult_numba((a[3], a[8]))) - Fraction(1, mult_numba((a[4], a[8]))) - Fraction(1, mult_numba((a[5], a[8]))) - Fraction(1, mult_numba((a[6], a[8]))) - Fraction(1, mult_numba((a[7], a[8]))) + Fraction(1, mult_numba((a[0], a[1], a[8]))) + Fraction(1, mult_numba((a[0], a[2], a[8]))) + Fraction(1, mult_numba((a[0], a[3], a[8]))) + Fraction(1, mult_numba((a[0], a[4], a[8]))) + Fraction(1, mult_numba((a[0], a[5], a[8]))) + Fraction(1, mult_numba((a[0], a[6], a[8]))) + Fraction(1, mult_numba((a[0], a[7], a[8]))) + Fraction(1, mult_numba((a[1], a[2], a[8]))) + Fraction(1, mult_numba((a[1], a[3], a[8]))) + Fraction(1, mult_numba((a[1], a[4], a[8]))) + Fraction(1, mult_numba((a[1], a[5], a[8]))) + Fraction(1, mult_numba((a[1], a[6], a[8]))) + Fraction(1, mult_numba((a[1], a[7], a[8]))) + Fraction(1, mult_numba((a[2], a[3], a[8]))) + Fraction(1, mult_numba((a[2], a[4], a[8]))) + Fraction(1, mult_numba((a[2], a[5], a[8]))) + Fraction(1, mult_numba((a[2], a[6], a[8]))) + Fraction(1, mult_numba((a[2], a[7], a[8]))) + Fraction(1, mult_numba((a[3], a[4], a[8]))) + Fraction(1, mult_numba((a[3], a[5], a[8]))) + Fraction(1, mult_numba((a[3], a[6], a[8]))) + Fraction(1, mult_numba((a[3], a[7], a[8]))) + Fraction(1, mult_numba((a[4], a[5], a[8]))) + Fraction(1, mult_numba((a[4], a[6], a[8]))) + Fraction(1, mult_numba((a[4], a[7], a[8]))) + Fraction(1, mult_numba((a[5], a[6], a[8]))) + Fraction(1, mult_numba((a[5], a[7], a[8]))) + Fraction(1, mult_numba((a[6], a[7], a[8]))) - Fraction(1, mult_numba((a[0], a[1], a[2], a[8]))) - Fraction(1, mult_numba((a[0], a[1], a[3], a[8]))) - Fraction(1, mult_numba((a[0], a[1], a[4], a[8]))) - Fraction(1, mult_numba((a[0], a[1], a[5], a[8]))) - Fraction(1, mult_numba((a[0], a[1], a[6], a[8]))) - Fraction(1, mult_numba((a[0], a[1], a[7], a[8]))) - Fraction(1, mult_numba((a[0], a[2], a[3], a[8]))) - Fraction(1, mult_numba((a[0], a[2], a[4], a[8]))) - Fraction(1, mult_numba((a[0], a[2], a[5], a[8]))) - Fraction(1, mult_numba((a[0], a[2], a[6], a[8]))) - Fraction(1, mult_numba((a[0], a[2], a[7], a[8]))) - Fraction(1, mult_numba((a[0], a[3], a[4], a[8]))) - Fraction(1, mult_numba((a[0], a[3], a[5], a[8]))) - Fraction(1, mult_numba((a[0], a[3], a[6], a[8]))) - Fraction(1, mult_numba((a[0], a[3], a[7], a[8]))) - Fraction(1, mult_numba((a[0], a[4], a[5], a[8]))) - Fraction(1, mult_numba((a[0], a[4], a[6], a[8]))) - Fraction(1, mult_numba((a[0], a[4], a[7], a[8]))) - Fraction(1, mult_numba((a[0], a[5], a[6], a[8]))) - Fraction(1, mult_numba((a[0], a[5], a[7], a[8]))) - Fraction(1, mult_numba((a[0], a[6], a[7], a[8]))) - Fraction(1, mult_numba((a[1], a[2], a[3], a[8]))) - Fraction(1, mult_numba((a[1], a[2], a[4], a[8]))) - Fraction(1, mult_numba((a[1], a[2], a[5], a[8]))) - Fraction(1, mult_numba((a[1], a[2], a[6], a[8]))) - Fraction(1, mult_numba((a[1], a[2], a[7], a[8]))) - Fraction(1, mult_numba((a[1], a[3], a[4], a[8]))) - Fraction(1, mult_numba((a[1], a[3], a[5], a[8]))) - Fraction(1, mult_numba((a[1], a[3], a[6], a[8]))) - Fraction(1, mult_numba((a[1], a[3], a[7], a[8]))) - Fraction(1, mult_numba((a[1], a[4], a[5], a[8]))) - Fraction(1, mult_numba((a[1], a[4], a[6], a[8]))) - Fraction(1, mult_numba((a[1], a[4], a[7], a[8]))) - Fraction(1, mult_numba((a[1], a[5], a[6], a[8]))) - Fraction(1, mult_numba((a[1], a[5], a[7], a[8]))) - Fraction(1, mult_numba((a[1], a[6], a[7], a[8]))) - Fraction(1, mult_numba((a[2], a[3], a[4], a[8]))) - Fraction(1, mult_numba((a[2], a[3], a[5], a[8]))) - Fraction(1, mult_numba((a[2], a[3], a[6], a[8]))) - Fraction(1, mult_numba((a[2], a[3], a[7], a[8]))) - Fraction(1, mult_numba((a[2], a[4], a[5], a[8]))) - Fraction(1, mult_numba((a[2], a[4], a[6], a[8]))) - Fraction(1, mult_numba((a[2], a[4], a[7], a[8]))) - Fraction(1, mult_numba((a[2], a[5], a[6], a[8]))) - Fraction(1, mult_numba((a[2], a[5], a[7], a[8]))) - Fraction(1, mult_numba((a[2], a[6], a[7], a[8]))) - Fraction(1, mult_numba((a[3], a[4], a[5], a[8]))) - Fraction(1, mult_numba((a[3], a[4], a[6], a[8]))) - Fraction(1, mult_numba((a[3], a[4], a[7], a[8]))) - Fraction(1, mult_numba((a[3], a[5], a[6], a[8]))) - Fraction(1, mult_numba((a[3], a[5], a[7], a[8]))) - Fraction(1, mult_numba((a[3], a[6], a[7], a[8]))) - Fraction(1, mult_numba((a[4], a[5], a[6], a[8]))) - Fraction(1, mult_numba((a[4], a[5], a[7], a[8]))) - Fraction(1, mult_numba((a[4], a[6], a[7], a[8]))) - Fraction(1, mult_numba((a[5], a[6], a[7], a[8]))) + Fraction(1, mult_numba((a[0], a[1], a[2], a[3], a[8]))) + Fraction(1, mult_numba((a[0], a[1], a[2], a[4], a[8]))) + Fraction(1, mult_numba((a[0], a[1], a[2], a[5], a[8]))) + Fraction(1, mult_numba((a[0], a[1], a[2], a[6], a[8]))) + Fraction(1, mult_numba((a[0], a[1], a[2], a[7], a[8]))) + Fraction(1, mult_numba((a[0], a[1], a[3], a[4], a[8]))) + Fraction(1, mult_numba((a[0], a[1], a[3], a[5], a[8]))) + Fraction(1, mult_numba((a[0], a[1], a[3], a[6], a[8]))) + Fraction(1, mult_numba((a[0], a[1], a[3], a[7], a[8]))) + Fraction(1, mult_numba((a[0], a[1], a[4], a[5], a[8]))) + Fraction(1, mult_numba((a[0], a[1], a[4], a[6], a[8]))) + Fraction(1, mult_numba((a[0], a[1], a[4], a[7], a[8]))) + Fraction(1, mult_numba((a[0], a[1], a[5], a[6], a[8]))) + Fraction(1, mult_numba((a[0], a[1], a[5], a[7], a[8]))) + Fraction(1, mult_numba((a[0], a[1], a[6], a[7], a[8]))) + Fraction(1, mult_numba((a[0], a[2], a[3], a[4], a[8]))) + Fraction(1, mult_numba((a[0], a[2], a[3], a[5], a[8]))) + Fraction(1, mult_numba((a[0], a[2], a[3], a[6], a[8]))) + Fraction(1, mult_numba((a[0], a[2], a[3], a[7], a[8]))) + Fraction(1, mult_numba((a[0], a[2], a[4], a[5], a[8]))) + Fraction(1, mult_numba((a[0], a[2], a[4], a[6], a[8]))) + Fraction(1, mult_numba((a[0], a[2], a[4], a[7], a[8]))) + Fraction(1, mult_numba((a[0], a[2], a[5], a[6], a[8]))) + Fraction(1, mult_numba((a[0], a[2], a[5], a[7], a[8]))) + Fraction(1, mult_numba((a[0], a[2], a[6], a[7], a[8]))) + Fraction(1, mult_numba((a[0], a[3], a[4], a[5], a[8]))) + Fraction(1, mult_numba((a[0], a[3], a[4], a[6], a[8]))) + Fraction(1, mult_numba((a[0], a[3], a[4], a[7], a[8]))) + Fraction(1, mult_numba((a[0], a[3], a[5], a[6], a[8]))) + Fraction(1, mult_numba((a[0], a[3], a[5], a[7], a[8]))) + Fraction(1, mult_numba((a[0], a[3], a[6], a[7], a[8]))) + Fraction(1, mult_numba((a[0], a[4], a[5], a[6], a[8]))) + Fraction(1, mult_numba((a[0], a[4], a[5], a[7], a[8]))) + Fraction(1, mult_numba((a[0], a[4], a[6], a[7], a[8]))) + Fraction(1, mult_numba((a[0], a[5], a[6], a[7], a[8]))) + Fraction(1, mult_numba((a[1], a[2], a[3], a[4], a[8]))) + Fraction(1, mult_numba((a[1], a[2], a[3], a[5], a[8]))) + Fraction(1, mult_numba((a[1], a[2], a[3], a[6], a[8]))) + Fraction(1, mult_numba((a[1], a[2], a[3], a[7], a[8]))) + Fraction(1, mult_numba((a[1], a[2], a[4], a[5], a[8]))) + Fraction(1, mult_numba((a[1], a[2], a[4], a[6], a[8]))) + Fraction(1, mult_numba((a[1], a[2], a[4], a[7], a[8]))) + Fraction(1, mult_numba((a[1], a[2], a[5], a[6], a[8]))) + Fraction(1, mult_numba((a[1], a[2], a[5], a[7], a[8]))) + Fraction(1, mult_numba((a[1], a[2], a[6], a[7], a[8]))) + Fraction(1, mult_numba((a[1], a[3], a[4], a[5], a[8]))) + Fraction(1, mult_numba((a[1], a[3], a[4], a[6], a[8]))) + Fraction(1, mult_numba((a[1], a[3], a[4], a[7], a[8]))) + Fraction(1, mult_numba((a[1], a[3], a[5], a[6], a[8]))) + Fraction(1, mult_numba((a[1], a[3], a[5], a[7], a[8]))) + Fraction(1, mult_numba((a[1], a[3], a[6], a[7], a[8]))) + Fraction(1, mult_numba((a[1], a[4], a[5], a[6], a[8]))) + Fraction(1, mult_numba((a[1], a[4], a[5], a[7], a[8]))) + Fraction(1, mult_numba((a[1], a[4], a[6], a[7], a[8]))) + Fraction(1, mult_numba((a[1], a[5], a[6], a[7], a[8]))) + Fraction(1, mult_numba((a[2], a[3], a[4], a[5], a[8]))) + Fraction(1, mult_numba((a[2], a[3], a[4], a[6], a[8]))) + Fraction(1, mult_numba((a[2], a[3], a[4], a[7], a[8]))) + Fraction(1, mult_numba((a[2], a[3], a[5], a[6], a[8]))) + Fraction(1, mult_numba((a[2], a[3], a[5], a[7], a[8]))) + Fraction(1, mult_numba((a[2], a[3], a[6], a[7], a[8]))) + Fraction(1, mult_numba((a[2], a[4], a[5], a[6], a[8]))) + Fraction(1, mult_numba((a[2], a[4], a[5], a[7], a[8]))) + Fraction(1, mult_numba((a[2], a[4], a[6], a[7], a[8]))) + Fraction(1, mult_numba((a[2], a[5], a[6], a[7], a[8]))) + Fraction(1, mult_numba((a[3], a[4], a[5], a[6], a[8]))) + Fraction(1, mult_numba((a[3], a[4], a[5], a[7], a[8]))) + Fraction(1, mult_numba((a[3], a[4], a[6], a[7], a[8]))) + Fraction(1, mult_numba((a[3], a[5], a[6], a[7], a[8]))) + Fraction(1, mult_numba((a[4], a[5], a[6], a[7], a[8]))) - Fraction(1, mult_numba((a[0], a[1], a[2], a[3], a[4], a[8]))) - Fraction(1, mult_numba((a[0], a[1], a[2], a[3], a[5], a[8]))) - Fraction(1, mult_numba((a[0], a[1], a[2], a[3], a[6], a[8])))
		frac += Fraction(-1, mult_numba((a[0], a[1], a[2], a[3], a[7], a[8]))) - Fraction(1, mult_numba((a[0], a[1], a[2], a[4], a[5], a[8]))) - Fraction(1, mult_numba((a[0], a[1], a[2], a[4], a[6], a[8]))) - Fraction(1, mult_numba((a[0], a[1], a[2], a[4], a[7], a[8]))) - Fraction(1, mult_numba((a[0], a[1], a[2], a[5], a[6], a[8]))) - Fraction(1, mult_numba((a[0], a[1], a[2], a[5], a[7], a[8]))) - Fraction(1, mult_numba((a[0], a[1], a[2], a[6], a[7], a[8]))) - Fraction(1, mult_numba((a[0], a[1], a[3], a[4], a[5], a[8]))) - Fraction(1, mult_numba((a[0], a[1], a[3], a[4], a[6], a[8]))) - Fraction(1, mult_numba((a[0], a[1], a[3], a[4], a[7], a[8]))) - Fraction(1, mult_numba((a[0], a[1], a[3], a[5], a[6], a[8]))) - Fraction(1, mult_numba((a[0], a[1], a[3], a[5], a[7], a[8]))) - Fraction(1, mult_numba((a[0], a[1], a[3], a[6], a[7], a[8]))) - Fraction(1, mult_numba((a[0], a[1], a[4], a[5], a[6], a[8]))) - Fraction(1, mult_numba((a[0], a[1], a[4], a[5], a[7], a[8]))) - Fraction(1, mult_numba((a[0], a[1], a[4], a[6], a[7], a[8]))) - Fraction(1, mult_numba((a[0], a[1], a[5], a[6], a[7], a[8]))) - Fraction(1, mult_numba((a[0], a[2], a[3], a[4], a[5], a[8]))) - Fraction(1, mult_numba((a[0], a[2], a[3], a[4], a[6], a[8]))) - Fraction(1, mult_numba((a[0], a[2], a[3], a[4], a[7], a[8]))) - Fraction(1, mult_numba((a[0], a[2], a[3], a[5], a[6], a[8]))) - Fraction(1, mult_numba((a[0], a[2], a[3], a[5], a[7], a[8]))) - Fraction(1, mult_numba((a[0], a[2], a[3], a[6], a[7], a[8]))) - Fraction(1, mult_numba((a[0], a[2], a[4], a[5], a[6], a[8]))) - Fraction(1, mult_numba((a[0], a[2], a[4], a[5], a[7], a[8]))) - Fraction(1, mult_numba((a[0], a[2], a[4], a[6], a[7], a[8]))) - Fraction(1, mult_numba((a[0], a[2], a[5], a[6], a[7], a[8]))) - Fraction(1, mult_numba((a[0], a[3], a[4], a[5], a[6], a[8]))) - Fraction(1, mult_numba((a[0], a[3], a[4], a[5], a[7], a[8]))) - Fraction(1, mult_numba((a[0], a[3], a[4], a[6], a[7], a[8]))) - Fraction(1, mult_numba((a[0], a[3], a[5], a[6], a[7], a[8]))) - Fraction(1, mult_numba((a[0], a[4], a[5], a[6], a[7], a[8]))) - Fraction(1, mult_numba((a[1], a[2], a[3], a[4], a[5], a[8]))) - Fraction(1, mult_numba((a[1], a[2], a[3], a[4], a[6], a[8]))) - Fraction(1, mult_numba((a[1], a[2], a[3], a[4], a[7], a[8]))) - Fraction(1, mult_numba((a[1], a[2], a[3], a[5], a[6], a[8]))) - Fraction(1, mult_numba((a[1], a[2], a[3], a[5], a[7], a[8]))) - Fraction(1, mult_numba((a[1], a[2], a[3], a[6], a[7], a[8]))) - Fraction(1, mult_numba((a[1], a[2], a[4], a[5], a[6], a[8]))) - Fraction(1, mult_numba((a[1], a[2], a[4], a[5], a[7], a[8]))) - Fraction(1, mult_numba((a[1], a[2], a[4], a[6], a[7], a[8]))) - Fraction(1, mult_numba((a[1], a[2], a[5], a[6], a[7], a[8]))) - Fraction(1, mult_numba((a[1], a[3], a[4], a[5], a[6], a[8]))) - Fraction(1, mult_numba((a[1], a[3], a[4], a[5], a[7], a[8]))) - Fraction(1, mult_numba((a[1], a[3], a[4], a[6], a[7], a[8]))) - Fraction(1, mult_numba((a[1], a[3], a[5], a[6], a[7], a[8]))) - Fraction(1, mult_numba((a[1], a[4], a[5], a[6], a[7], a[8]))) - Fraction(1, mult_numba((a[2], a[3], a[4], a[5], a[6], a[8]))) - Fraction(1, mult_numba((a[2], a[3], a[4], a[5], a[7], a[8]))) - Fraction(1, mult_numba((a[2], a[3], a[4], a[6], a[7], a[8]))) - Fraction(1, mult_numba((a[2], a[3], a[5], a[6], a[7], a[8]))) - Fraction(1, mult_numba((a[2], a[4], a[5], a[6], a[7], a[8]))) - Fraction(1, mult_numba((a[3], a[4], a[5], a[6], a[7], a[8]))) + Fraction(1, mult_numba((a[0], a[1], a[2], a[3], a[4], a[5], a[8]))) + Fraction(1, mult_numba((a[0], a[1], a[2], a[3], a[4], a[6], a[8]))) + Fraction(1, mult_numba((a[0], a[1], a[2], a[3], a[4], a[7], a[8]))) + Fraction(1, mult_numba((a[0], a[1], a[2], a[3], a[5], a[6], a[8]))) + Fraction(1, mult_numba((a[0], a[1], a[2], a[3], a[5], a[7], a[8]))) + Fraction(1, mult_numba((a[0], a[1], a[2], a[3], a[6], a[7], a[8]))) + Fraction(1, mult_numba((a[0], a[1], a[2], a[4], a[5], a[6], a[8]))) + Fraction(1, mult_numba((a[0], a[1], a[2], a[4], a[5], a[7], a[8]))) + Fraction(1, mult_numba((a[0], a[1], a[2], a[4], a[6], a[7], a[8]))) + Fraction(1, mult_numba((a[0], a[1], a[2], a[5], a[6], a[7], a[8]))) + Fraction(1, mult_numba((a[0], a[1], a[3], a[4], a[5], a[6], a[8]))) + Fraction(1, mult_numba((a[0], a[1], a[3], a[4], a[5], a[7], a[8]))) + Fraction(1, mult_numba((a[0], a[1], a[3], a[4], a[6], a[7], a[8]))) + Fraction(1, mult_numba((a[0], a[1], a[3], a[5], a[6], a[7], a[8]))) + Fraction(1, mult_numba((a[0], a[1], a[4], a[5], a[6], a[7], a[8]))) + Fraction(1, mult_numba((a[0], a[2], a[3], a[4], a[5], a[6], a[8]))) + Fraction(1, mult_numba((a[0], a[2], a[3], a[4], a[5], a[7], a[8]))) + Fraction(1, mult_numba((a[0], a[2], a[3], a[4], a[6], a[7], a[8]))) + Fraction(1, mult_numba((a[0], a[2], a[3], a[5], a[6], a[7], a[8]))) + Fraction(1, mult_numba((a[0], a[2], a[4], a[5], a[6], a[7], a[8]))) + Fraction(1, mult_numba((a[0], a[3], a[4], a[5], a[6], a[7], a[8]))) + Fraction(1, mult_numba((a[1], a[2], a[3], a[4], a[5], a[6], a[8]))) + Fraction(1, mult_numba((a[1], a[2], a[3], a[4], a[5], a[7], a[8]))) + Fraction(1, mult_numba((a[1], a[2], a[3], a[4], a[6], a[7], a[8]))) + Fraction(1, mult_numba((a[1], a[2], a[3], a[5], a[6], a[7], a[8]))) + Fraction(1, mult_numba((a[1], a[2], a[4], a[5], a[6], a[7], a[8]))) + Fraction(1, mult_numba((a[1], a[3], a[4], a[5], a[6], a[7], a[8]))) + Fraction(1, mult_numba((a[2], a[3], a[4], a[5], a[6], a[7], a[8]))) - Fraction(1, mult_numba((a[0], a[1], a[2], a[3], a[4], a[5], a[6], a[8]))) - Fraction(1, mult_numba((a[0], a[1], a[2], a[3], a[4], a[5], a[7], a[8]))) - Fraction(1, mult_numba((a[0], a[1], a[2], a[3], a[4], a[6], a[7], a[8]))) - Fraction(1, mult_numba((a[0], a[1], a[2], a[3], a[5], a[6], a[7], a[8]))) - Fraction(1, mult_numba((a[0], a[1], a[2], a[4], a[5], a[6], a[7], a[8]))) - Fraction(1, mult_numba((a[0], a[1], a[3], a[4], a[5], a[6], a[7], a[8]))) - Fraction(1, mult_numba((a[0], a[2], a[3], a[4], a[5], a[6], a[7], a[8]))) - Fraction(1, mult_numba((a[1], a[2], a[3], a[4], a[5], a[6], a[7], a[8]))) + Fraction(1, mult_numba(a[0:9]))
		if bcheckmax and frac > max_sum:
			return Fraction(1, 1)
	return frac
	

#import sys, fractions
#sys.path.append(r"D:\Python\Sequence")
#import sequence_th as seq
#seq.calc_density_python(24, [4, 6], fractions.Fraction(1, 1))
def calc_density_python(i, a, max_sum):
	#print(f"calc_density_python({i}, {a}, {max_sum})")
	bcheckmax = False
	ilen = len(a)
	frac = fractions.Fraction(1, a[0])
	if frac > max_sum:
		return fractions.Fraction(1, 1)
	frac += fractions.Fraction(1, a[1]) - fractions.Fraction(1, mult(a[0:2]))
	if bcheckmax and frac > max_sum:
		return fractions.Fraction(1, 1)
	if ilen >= 3:
		frac += fractions.Fraction(1, a[2]) - fractions.Fraction(1, mult((a[0], a[2]))) - fractions.Fraction(1, mult((a[1], a[2]))) + fractions.Fraction(1, mult(a[0:3]))
		if bcheckmax and frac > max_sum:
			return fractions.Fraction(1, 1)
	if ilen >= 4:
		frac += fractions.Fraction(1, a[3]) - fractions.Fraction(1, mult((a[0], a[3]))) - fractions.Fraction(1, mult((a[1], a[3]))) - fractions.Fraction(1, mult((a[2], a[3]))) + fractions.Fraction(1, mult((a[0], a[1], a[3]))) + fractions.Fraction(1, mult((a[0], a[2], a[3]))) + fractions.Fraction(1, mult((a[1], a[2], a[3]))) - fractions.Fraction(1, mult(a[0:4]))
		if bcheckmax and frac > max_sum:
			return fractions.Fraction(1, 1)
	if ilen >= 5:
		frac += fractions.Fraction(1, a[4]) - fractions.Fraction(1, mult((a[0], a[4]))) - fractions.Fraction(1, mult((a[1], a[4]))) - fractions.Fraction(1, mult((a[2], a[4]))) - fractions.Fraction(1, mult((a[3], a[4]))) + fractions.Fraction(1, mult((a[0], a[1], a[4]))) + fractions.Fraction(1, mult((a[0], a[2], a[4]))) + fractions.Fraction(1, mult((a[0], a[3], a[4]))) + fractions.Fraction(1, mult((a[1], a[2], a[4]))) + fractions.Fraction(1, mult((a[1], a[3], a[4]))) + fractions.Fraction(1, mult((a[2], a[3], a[4]))) - fractions.Fraction(1, mult((a[0], a[1], a[2], a[4]))) - fractions.Fraction(1, mult((a[0], a[1], a[3], a[4]))) - fractions.Fraction(1, mult((a[0], a[2], a[3], a[4]))) - fractions.Fraction(1, mult((a[1], a[2], a[3], a[4]))) + fractions.Fraction(1, mult(a[0:5]))
		if bcheckmax and frac > max_sum:
			return fractions.Fraction(1, 1)
	if ilen >= 6:
		frac += fractions.Fraction(1, a[5]) - fractions.Fraction(1, mult((a[0], a[5]))) - fractions.Fraction(1, mult((a[1], a[5]))) - fractions.Fraction(1, mult((a[2], a[5]))) - fractions.Fraction(1, mult((a[3], a[5]))) - fractions.Fraction(1, mult((a[4], a[5]))) + fractions.Fraction(1, mult((a[0], a[1], a[5]))) + fractions.Fraction(1, mult((a[0], a[2], a[5]))) + fractions.Fraction(1, mult((a[0], a[3], a[5]))) + fractions.Fraction(1, mult((a[0], a[4], a[5]))) + fractions.Fraction(1, mult((a[1], a[2], a[5]))) + fractions.Fraction(1, mult((a[1], a[3], a[5]))) + fractions.Fraction(1, mult((a[1], a[4], a[5]))) + fractions.Fraction(1, mult((a[2], a[3], a[5]))) + fractions.Fraction(1, mult((a[2], a[4], a[5]))) + fractions.Fraction(1, mult((a[3], a[4], a[5]))) - fractions.Fraction(1, mult((a[0], a[1], a[2], a[5]))) - fractions.Fraction(1, mult((a[0], a[1], a[3], a[5]))) - fractions.Fraction(1, mult((a[0], a[1], a[4], a[5]))) - fractions.Fraction(1, mult((a[0], a[2], a[3], a[5]))) - fractions.Fraction(1, mult((a[0], a[2], a[4], a[5]))) - fractions.Fraction(1, mult((a[0], a[3], a[4], a[5]))) - fractions.Fraction(1, mult((a[1], a[2], a[3], a[5]))) - fractions.Fraction(1, mult((a[1], a[2], a[4], a[5]))) - fractions.Fraction(1, mult((a[1], a[3], a[4], a[5]))) - fractions.Fraction(1, mult((a[2], a[3], a[4], a[5]))) + fractions.Fraction(1, mult((a[0], a[1], a[2], a[3], a[5]))) + fractions.Fraction(1, mult((a[0], a[1], a[2], a[4], a[5]))) + fractions.Fraction(1, mult((a[0], a[1], a[3], a[4], a[5]))) + fractions.Fraction(1, mult((a[0], a[2], a[3], a[4], a[5]))) + fractions.Fraction(1, mult((a[1], a[2], a[3], a[4], a[5]))) - fractions.Fraction(1, mult(a[0:6]))
		if bcheckmax and frac > max_sum:
			return fractions.Fraction(1, 1)
	if ilen >= 7:
		frac += fractions.Fraction(1, a[6]) - fractions.Fraction(1, mult((a[0], a[6]))) - fractions.Fraction(1, mult((a[1], a[6]))) - fractions.Fraction(1, mult((a[2], a[6]))) - fractions.Fraction(1, mult((a[3], a[6]))) - fractions.Fraction(1, mult((a[4], a[6]))) - fractions.Fraction(1, mult((a[5], a[6]))) + fractions.Fraction(1, mult((a[0], a[1], a[6]))) + fractions.Fraction(1, mult((a[0], a[2], a[6]))) + fractions.Fraction(1, mult((a[0], a[3], a[6]))) + fractions.Fraction(1, mult((a[0], a[4], a[6]))) + fractions.Fraction(1, mult((a[0], a[5], a[6]))) + fractions.Fraction(1, mult((a[1], a[2], a[6]))) + fractions.Fraction(1, mult((a[1], a[3], a[6]))) + fractions.Fraction(1, mult((a[1], a[4], a[6]))) + fractions.Fraction(1, mult((a[1], a[5], a[6]))) + fractions.Fraction(1, mult((a[2], a[3], a[6]))) + fractions.Fraction(1, mult((a[2], a[4], a[6]))) + fractions.Fraction(1, mult((a[2], a[5], a[6]))) + fractions.Fraction(1, mult((a[3], a[4], a[6]))) + fractions.Fraction(1, mult((a[3], a[5], a[6]))) + fractions.Fraction(1, mult((a[4], a[5], a[6]))) - fractions.Fraction(1, mult((a[0], a[1], a[2], a[6]))) - fractions.Fraction(1, mult((a[0], a[1], a[3], a[6]))) - fractions.Fraction(1, mult((a[0], a[1], a[4], a[6]))) - fractions.Fraction(1, mult((a[0], a[1], a[5], a[6]))) - fractions.Fraction(1, mult((a[0], a[2], a[3], a[6]))) - fractions.Fraction(1, mult((a[0], a[2], a[4], a[6]))) - fractions.Fraction(1, mult((a[0], a[2], a[5], a[6]))) - fractions.Fraction(1, mult((a[0], a[3], a[4], a[6]))) - fractions.Fraction(1, mult((a[0], a[3], a[5], a[6]))) - fractions.Fraction(1, mult((a[0], a[4], a[5], a[6]))) - fractions.Fraction(1, mult((a[1], a[2], a[3], a[6]))) - fractions.Fraction(1, mult((a[1], a[2], a[4], a[6]))) - fractions.Fraction(1, mult((a[1], a[2], a[5], a[6]))) - fractions.Fraction(1, mult((a[1], a[3], a[4], a[6]))) - fractions.Fraction(1, mult((a[1], a[3], a[5], a[6]))) - fractions.Fraction(1, mult((a[1], a[4], a[5], a[6]))) - fractions.Fraction(1, mult((a[2], a[3], a[4], a[6]))) - fractions.Fraction(1, mult((a[2], a[3], a[5], a[6]))) - fractions.Fraction(1, mult((a[2], a[4], a[5], a[6]))) - fractions.Fraction(1, mult((a[3], a[4], a[5], a[6]))) + fractions.Fraction(1, mult((a[0], a[1], a[2], a[3], a[6]))) + fractions.Fraction(1, mult((a[0], a[1], a[2], a[4], a[6]))) + fractions.Fraction(1, mult((a[0], a[1], a[2], a[5], a[6]))) + fractions.Fraction(1, mult((a[0], a[1], a[3], a[4], a[6]))) + fractions.Fraction(1, mult((a[0], a[1], a[3], a[5], a[6]))) + fractions.Fraction(1, mult((a[0], a[1], a[4], a[5], a[6]))) + fractions.Fraction(1, mult((a[0], a[2], a[3], a[4], a[6]))) + fractions.Fraction(1, mult((a[0], a[2], a[3], a[5], a[6]))) + fractions.Fraction(1, mult((a[0], a[2], a[4], a[5], a[6]))) + fractions.Fraction(1, mult((a[0], a[3], a[4], a[5], a[6]))) + fractions.Fraction(1, mult((a[1], a[2], a[3], a[4], a[6]))) + fractions.Fraction(1, mult((a[1], a[2], a[3], a[5], a[6]))) + fractions.Fraction(1, mult((a[1], a[2], a[4], a[5], a[6]))) + fractions.Fraction(1, mult((a[1], a[3], a[4], a[5], a[6]))) + fractions.Fraction(1, mult((a[2], a[3], a[4], a[5], a[6]))) - fractions.Fraction(1, mult((a[0], a[1], a[2], a[3], a[4], a[6]))) - fractions.Fraction(1, mult((a[0], a[1], a[2], a[3], a[5], a[6]))) - fractions.Fraction(1, mult((a[0], a[1], a[2], a[4], a[5], a[6]))) - fractions.Fraction(1, mult((a[0], a[1], a[3], a[4], a[5], a[6]))) - fractions.Fraction(1, mult((a[0], a[2], a[3], a[4], a[5], a[6]))) - fractions.Fraction(1, mult((a[1], a[2], a[3], a[4], a[5], a[6]))) + fractions.Fraction(1, mult(a[0:7]))
		if bcheckmax and frac > max_sum:
			return fractions.Fraction(1, 1)
	if ilen >= 8:
		frac += fractions.Fraction(1, a[7]) - fractions.Fraction(1, mult((a[0], a[7]))) - fractions.Fraction(1, mult((a[1], a[7]))) - fractions.Fraction(1, mult((a[2], a[7]))) - fractions.Fraction(1, mult((a[3], a[7]))) - fractions.Fraction(1, mult((a[4], a[7]))) - fractions.Fraction(1, mult((a[5], a[7]))) - fractions.Fraction(1, mult((a[6], a[7]))) + fractions.Fraction(1, mult((a[0], a[1], a[7]))) + fractions.Fraction(1, mult((a[0], a[2], a[7]))) + fractions.Fraction(1, mult((a[0], a[3], a[7]))) + fractions.Fraction(1, mult((a[0], a[4], a[7]))) + fractions.Fraction(1, mult((a[0], a[5], a[7]))) + fractions.Fraction(1, mult((a[0], a[6], a[7]))) + fractions.Fraction(1, mult((a[1], a[2], a[7]))) + fractions.Fraction(1, mult((a[1], a[3], a[7]))) + fractions.Fraction(1, mult((a[1], a[4], a[7]))) + fractions.Fraction(1, mult((a[1], a[5], a[7]))) + fractions.Fraction(1, mult((a[1], a[6], a[7]))) + fractions.Fraction(1, mult((a[2], a[3], a[7]))) + fractions.Fraction(1, mult((a[2], a[4], a[7]))) + fractions.Fraction(1, mult((a[2], a[5], a[7]))) + fractions.Fraction(1, mult((a[2], a[6], a[7]))) + fractions.Fraction(1, mult((a[3], a[4], a[7]))) + fractions.Fraction(1, mult((a[3], a[5], a[7]))) + fractions.Fraction(1, mult((a[3], a[6], a[7]))) + fractions.Fraction(1, mult((a[4], a[5], a[7]))) + fractions.Fraction(1, mult((a[4], a[6], a[7]))) + fractions.Fraction(1, mult((a[5], a[6], a[7]))) - fractions.Fraction(1, mult((a[0], a[1], a[2], a[7]))) - fractions.Fraction(1, mult((a[0], a[1], a[3], a[7]))) - fractions.Fraction(1, mult((a[0], a[1], a[4], a[7]))) - fractions.Fraction(1, mult((a[0], a[1], a[5], a[7]))) - fractions.Fraction(1, mult((a[0], a[1], a[6], a[7]))) - fractions.Fraction(1, mult((a[0], a[2], a[3], a[7]))) - fractions.Fraction(1, mult((a[0], a[2], a[4], a[7]))) - fractions.Fraction(1, mult((a[0], a[2], a[5], a[7]))) - fractions.Fraction(1, mult((a[0], a[2], a[6], a[7]))) - fractions.Fraction(1, mult((a[0], a[3], a[4], a[7]))) - fractions.Fraction(1, mult((a[0], a[3], a[5], a[7]))) - fractions.Fraction(1, mult((a[0], a[3], a[6], a[7]))) - fractions.Fraction(1, mult((a[0], a[4], a[5], a[7]))) - fractions.Fraction(1, mult((a[0], a[4], a[6], a[7]))) - fractions.Fraction(1, mult((a[0], a[5], a[6], a[7]))) - fractions.Fraction(1, mult((a[1], a[2], a[3], a[7]))) - fractions.Fraction(1, mult((a[1], a[2], a[4], a[7]))) - fractions.Fraction(1, mult((a[1], a[2], a[5], a[7]))) - fractions.Fraction(1, mult((a[1], a[2], a[6], a[7]))) - fractions.Fraction(1, mult((a[1], a[3], a[4], a[7]))) - fractions.Fraction(1, mult((a[1], a[3], a[5], a[7]))) - fractions.Fraction(1, mult((a[1], a[3], a[6], a[7]))) - fractions.Fraction(1, mult((a[1], a[4], a[5], a[7]))) - fractions.Fraction(1, mult((a[1], a[4], a[6], a[7]))) - fractions.Fraction(1, mult((a[1], a[5], a[6], a[7]))) - fractions.Fraction(1, mult((a[2], a[3], a[4], a[7]))) - fractions.Fraction(1, mult((a[2], a[3], a[5], a[7]))) - fractions.Fraction(1, mult((a[2], a[3], a[6], a[7]))) - fractions.Fraction(1, mult((a[2], a[4], a[5], a[7]))) - fractions.Fraction(1, mult((a[2], a[4], a[6], a[7]))) - fractions.Fraction(1, mult((a[2], a[5], a[6], a[7]))) - fractions.Fraction(1, mult((a[3], a[4], a[5], a[7]))) - fractions.Fraction(1, mult((a[3], a[4], a[6], a[7]))) - fractions.Fraction(1, mult((a[3], a[5], a[6], a[7]))) - fractions.Fraction(1, mult((a[4], a[5], a[6], a[7]))) + fractions.Fraction(1, mult((a[0], a[1], a[2], a[3], a[7]))) + fractions.Fraction(1, mult((a[0], a[1], a[2], a[4], a[7]))) + fractions.Fraction(1, mult((a[0], a[1], a[2], a[5], a[7]))) + fractions.Fraction(1, mult((a[0], a[1], a[2], a[6], a[7]))) + fractions.Fraction(1, mult((a[0], a[1], a[3], a[4], a[7]))) + fractions.Fraction(1, mult((a[0], a[1], a[3], a[5], a[7]))) + fractions.Fraction(1, mult((a[0], a[1], a[3], a[6], a[7]))) + fractions.Fraction(1, mult((a[0], a[1], a[4], a[5], a[7])))
		frac += fractions.Fraction(1, mult((a[0], a[1], a[4], a[6], a[7]))) + fractions.Fraction(1, mult((a[0], a[1], a[5], a[6], a[7]))) + fractions.Fraction(1, mult((a[0], a[2], a[3], a[4], a[7]))) + fractions.Fraction(1, mult((a[0], a[2], a[3], a[5], a[7]))) + fractions.Fraction(1, mult((a[0], a[2], a[3], a[6], a[7]))) + fractions.Fraction(1, mult((a[0], a[2], a[4], a[5], a[7]))) + fractions.Fraction(1, mult((a[0], a[2], a[4], a[6], a[7]))) + fractions.Fraction(1, mult((a[0], a[2], a[5], a[6], a[7]))) + fractions.Fraction(1, mult((a[0], a[3], a[4], a[5], a[7]))) + fractions.Fraction(1, mult((a[0], a[3], a[4], a[6], a[7]))) + fractions.Fraction(1, mult((a[0], a[3], a[5], a[6], a[7]))) + fractions.Fraction(1, mult((a[0], a[4], a[5], a[6], a[7]))) + fractions.Fraction(1, mult((a[1], a[2], a[3], a[4], a[7]))) + fractions.Fraction(1, mult((a[1], a[2], a[3], a[5], a[7]))) + fractions.Fraction(1, mult((a[1], a[2], a[3], a[6], a[7]))) + fractions.Fraction(1, mult((a[1], a[2], a[4], a[5], a[7]))) + fractions.Fraction(1, mult((a[1], a[2], a[4], a[6], a[7]))) + fractions.Fraction(1, mult((a[1], a[2], a[5], a[6], a[7]))) + fractions.Fraction(1, mult((a[1], a[3], a[4], a[5], a[7]))) + fractions.Fraction(1, mult((a[1], a[3], a[4], a[6], a[7]))) + fractions.Fraction(1, mult((a[1], a[3], a[5], a[6], a[7]))) + fractions.Fraction(1, mult((a[1], a[4], a[5], a[6], a[7]))) + fractions.Fraction(1, mult((a[2], a[3], a[4], a[5], a[7]))) + fractions.Fraction(1, mult((a[2], a[3], a[4], a[6], a[7]))) + fractions.Fraction(1, mult((a[2], a[3], a[5], a[6], a[7]))) + fractions.Fraction(1, mult((a[2], a[4], a[5], a[6], a[7]))) + fractions.Fraction(1, mult((a[3], a[4], a[5], a[6], a[7]))) - fractions.Fraction(1, mult((a[0], a[1], a[2], a[3], a[4], a[7]))) - fractions.Fraction(1, mult((a[0], a[1], a[2], a[3], a[5], a[7]))) - fractions.Fraction(1, mult((a[0], a[1], a[2], a[3], a[6], a[7]))) - fractions.Fraction(1, mult((a[0], a[1], a[2], a[4], a[5], a[7]))) - fractions.Fraction(1, mult((a[0], a[1], a[2], a[4], a[6], a[7]))) - fractions.Fraction(1, mult((a[0], a[1], a[2], a[5], a[6], a[7]))) - fractions.Fraction(1, mult((a[0], a[1], a[3], a[4], a[5], a[7]))) - fractions.Fraction(1, mult((a[0], a[1], a[3], a[4], a[6], a[7]))) - fractions.Fraction(1, mult((a[0], a[1], a[3], a[5], a[6], a[7]))) - fractions.Fraction(1, mult((a[0], a[1], a[4], a[5], a[6], a[7]))) - fractions.Fraction(1, mult((a[0], a[2], a[3], a[4], a[5], a[7]))) - fractions.Fraction(1, mult((a[0], a[2], a[3], a[4], a[6], a[7]))) - fractions.Fraction(1, mult((a[0], a[2], a[3], a[5], a[6], a[7]))) - fractions.Fraction(1, mult((a[0], a[2], a[4], a[5], a[6], a[7]))) - fractions.Fraction(1, mult((a[0], a[3], a[4], a[5], a[6], a[7]))) - fractions.Fraction(1, mult((a[1], a[2], a[3], a[4], a[5], a[7]))) - fractions.Fraction(1, mult((a[1], a[2], a[3], a[4], a[6], a[7]))) - fractions.Fraction(1, mult((a[1], a[2], a[3], a[5], a[6], a[7]))) - fractions.Fraction(1, mult((a[1], a[2], a[4], a[5], a[6], a[7]))) - fractions.Fraction(1, mult((a[1], a[3], a[4], a[5], a[6], a[7]))) - fractions.Fraction(1, mult((a[2], a[3], a[4], a[5], a[6], a[7]))) + fractions.Fraction(1, mult((a[0], a[1], a[2], a[3], a[4], a[5], a[7]))) + fractions.Fraction(1, mult((a[0], a[1], a[2], a[3], a[4], a[6], a[7]))) + fractions.Fraction(1, mult((a[0], a[1], a[2], a[3], a[5], a[6], a[7]))) + fractions.Fraction(1, mult((a[0], a[1], a[2], a[4], a[5], a[6], a[7]))) + fractions.Fraction(1, mult((a[0], a[1], a[3], a[4], a[5], a[6], a[7]))) + fractions.Fraction(1, mult((a[0], a[2], a[3], a[4], a[5], a[6], a[7]))) + fractions.Fraction(1, mult((a[1], a[2], a[3], a[4], a[5], a[6], a[7]))) - fractions.Fraction(1, mult(a[0:8]))
		if bcheckmax and frac > max_sum:
			return fractions.Fraction(1, 1)
	if ilen >= 9:
		frac += fractions.Fraction(1, a[8]) - fractions.Fraction(1, mult((a[0], a[8]))) - fractions.Fraction(1, mult((a[1], a[8]))) - fractions.Fraction(1, mult((a[2], a[8]))) - fractions.Fraction(1, mult((a[3], a[8]))) - fractions.Fraction(1, mult((a[4], a[8]))) - fractions.Fraction(1, mult((a[5], a[8]))) - fractions.Fraction(1, mult((a[6], a[8]))) - fractions.Fraction(1, mult((a[7], a[8]))) + fractions.Fraction(1, mult((a[0], a[1], a[8]))) + fractions.Fraction(1, mult((a[0], a[2], a[8]))) + fractions.Fraction(1, mult((a[0], a[3], a[8]))) + fractions.Fraction(1, mult((a[0], a[4], a[8]))) + fractions.Fraction(1, mult((a[0], a[5], a[8]))) + fractions.Fraction(1, mult((a[0], a[6], a[8]))) + fractions.Fraction(1, mult((a[0], a[7], a[8]))) + fractions.Fraction(1, mult((a[1], a[2], a[8]))) + fractions.Fraction(1, mult((a[1], a[3], a[8]))) + fractions.Fraction(1, mult((a[1], a[4], a[8]))) + fractions.Fraction(1, mult((a[1], a[5], a[8]))) + fractions.Fraction(1, mult((a[1], a[6], a[8]))) + fractions.Fraction(1, mult((a[1], a[7], a[8]))) + fractions.Fraction(1, mult((a[2], a[3], a[8]))) + fractions.Fraction(1, mult((a[2], a[4], a[8]))) + fractions.Fraction(1, mult((a[2], a[5], a[8]))) + fractions.Fraction(1, mult((a[2], a[6], a[8]))) + fractions.Fraction(1, mult((a[2], a[7], a[8]))) + fractions.Fraction(1, mult((a[3], a[4], a[8]))) + fractions.Fraction(1, mult((a[3], a[5], a[8]))) + fractions.Fraction(1, mult((a[3], a[6], a[8]))) + fractions.Fraction(1, mult((a[3], a[7], a[8]))) + fractions.Fraction(1, mult((a[4], a[5], a[8]))) + fractions.Fraction(1, mult((a[4], a[6], a[8]))) + fractions.Fraction(1, mult((a[4], a[7], a[8]))) + fractions.Fraction(1, mult((a[5], a[6], a[8]))) + fractions.Fraction(1, mult((a[5], a[7], a[8]))) + fractions.Fraction(1, mult((a[6], a[7], a[8]))) - fractions.Fraction(1, mult((a[0], a[1], a[2], a[8]))) - fractions.Fraction(1, mult((a[0], a[1], a[3], a[8]))) - fractions.Fraction(1, mult((a[0], a[1], a[4], a[8]))) - fractions.Fraction(1, mult((a[0], a[1], a[5], a[8]))) - fractions.Fraction(1, mult((a[0], a[1], a[6], a[8]))) - fractions.Fraction(1, mult((a[0], a[1], a[7], a[8]))) - fractions.Fraction(1, mult((a[0], a[2], a[3], a[8]))) - fractions.Fraction(1, mult((a[0], a[2], a[4], a[8]))) - fractions.Fraction(1, mult((a[0], a[2], a[5], a[8]))) - fractions.Fraction(1, mult((a[0], a[2], a[6], a[8]))) - fractions.Fraction(1, mult((a[0], a[2], a[7], a[8]))) - fractions.Fraction(1, mult((a[0], a[3], a[4], a[8]))) - fractions.Fraction(1, mult((a[0], a[3], a[5], a[8]))) - fractions.Fraction(1, mult((a[0], a[3], a[6], a[8]))) - fractions.Fraction(1, mult((a[0], a[3], a[7], a[8]))) - fractions.Fraction(1, mult((a[0], a[4], a[5], a[8]))) - fractions.Fraction(1, mult((a[0], a[4], a[6], a[8]))) - fractions.Fraction(1, mult((a[0], a[4], a[7], a[8]))) - fractions.Fraction(1, mult((a[0], a[5], a[6], a[8]))) - fractions.Fraction(1, mult((a[0], a[5], a[7], a[8]))) - fractions.Fraction(1, mult((a[0], a[6], a[7], a[8]))) - fractions.Fraction(1, mult((a[1], a[2], a[3], a[8]))) - fractions.Fraction(1, mult((a[1], a[2], a[4], a[8]))) - fractions.Fraction(1, mult((a[1], a[2], a[5], a[8]))) - fractions.Fraction(1, mult((a[1], a[2], a[6], a[8]))) - fractions.Fraction(1, mult((a[1], a[2], a[7], a[8]))) - fractions.Fraction(1, mult((a[1], a[3], a[4], a[8]))) - fractions.Fraction(1, mult((a[1], a[3], a[5], a[8]))) - fractions.Fraction(1, mult((a[1], a[3], a[6], a[8]))) - fractions.Fraction(1, mult((a[1], a[3], a[7], a[8]))) - fractions.Fraction(1, mult((a[1], a[4], a[5], a[8]))) - fractions.Fraction(1, mult((a[1], a[4], a[6], a[8]))) - fractions.Fraction(1, mult((a[1], a[4], a[7], a[8]))) - fractions.Fraction(1, mult((a[1], a[5], a[6], a[8]))) - fractions.Fraction(1, mult((a[1], a[5], a[7], a[8]))) - fractions.Fraction(1, mult((a[1], a[6], a[7], a[8]))) - fractions.Fraction(1, mult((a[2], a[3], a[4], a[8]))) - fractions.Fraction(1, mult((a[2], a[3], a[5], a[8]))) - fractions.Fraction(1, mult((a[2], a[3], a[6], a[8]))) - fractions.Fraction(1, mult((a[2], a[3], a[7], a[8]))) - fractions.Fraction(1, mult((a[2], a[4], a[5], a[8]))) - fractions.Fraction(1, mult((a[2], a[4], a[6], a[8]))) - fractions.Fraction(1, mult((a[2], a[4], a[7], a[8]))) - fractions.Fraction(1, mult((a[2], a[5], a[6], a[8]))) - fractions.Fraction(1, mult((a[2], a[5], a[7], a[8]))) - fractions.Fraction(1, mult((a[2], a[6], a[7], a[8]))) - fractions.Fraction(1, mult((a[3], a[4], a[5], a[8]))) - fractions.Fraction(1, mult((a[3], a[4], a[6], a[8]))) - fractions.Fraction(1, mult((a[3], a[4], a[7], a[8]))) - fractions.Fraction(1, mult((a[3], a[5], a[6], a[8]))) - fractions.Fraction(1, mult((a[3], a[5], a[7], a[8]))) - fractions.Fraction(1, mult((a[3], a[6], a[7], a[8]))) - fractions.Fraction(1, mult((a[4], a[5], a[6], a[8]))) - fractions.Fraction(1, mult((a[4], a[5], a[7], a[8]))) - fractions.Fraction(1, mult((a[4], a[6], a[7], a[8]))) - fractions.Fraction(1, mult((a[5], a[6], a[7], a[8]))) + fractions.Fraction(1, mult((a[0], a[1], a[2], a[3], a[8]))) + fractions.Fraction(1, mult((a[0], a[1], a[2], a[4], a[8]))) + fractions.Fraction(1, mult((a[0], a[1], a[2], a[5], a[8]))) + fractions.Fraction(1, mult((a[0], a[1], a[2], a[6], a[8]))) + fractions.Fraction(1, mult((a[0], a[1], a[2], a[7], a[8]))) + fractions.Fraction(1, mult((a[0], a[1], a[3], a[4], a[8]))) + fractions.Fraction(1, mult((a[0], a[1], a[3], a[5], a[8]))) + fractions.Fraction(1, mult((a[0], a[1], a[3], a[6], a[8]))) + fractions.Fraction(1, mult((a[0], a[1], a[3], a[7], a[8]))) + fractions.Fraction(1, mult((a[0], a[1], a[4], a[5], a[8]))) + fractions.Fraction(1, mult((a[0], a[1], a[4], a[6], a[8]))) + fractions.Fraction(1, mult((a[0], a[1], a[4], a[7], a[8]))) + fractions.Fraction(1, mult((a[0], a[1], a[5], a[6], a[8]))) + fractions.Fraction(1, mult((a[0], a[1], a[5], a[7], a[8]))) + fractions.Fraction(1, mult((a[0], a[1], a[6], a[7], a[8]))) + fractions.Fraction(1, mult((a[0], a[2], a[3], a[4], a[8]))) + fractions.Fraction(1, mult((a[0], a[2], a[3], a[5], a[8]))) + fractions.Fraction(1, mult((a[0], a[2], a[3], a[6], a[8]))) + fractions.Fraction(1, mult((a[0], a[2], a[3], a[7], a[8]))) + fractions.Fraction(1, mult((a[0], a[2], a[4], a[5], a[8]))) + fractions.Fraction(1, mult((a[0], a[2], a[4], a[6], a[8]))) + fractions.Fraction(1, mult((a[0], a[2], a[4], a[7], a[8]))) + fractions.Fraction(1, mult((a[0], a[2], a[5], a[6], a[8]))) + fractions.Fraction(1, mult((a[0], a[2], a[5], a[7], a[8]))) + fractions.Fraction(1, mult((a[0], a[2], a[6], a[7], a[8]))) + fractions.Fraction(1, mult((a[0], a[3], a[4], a[5], a[8]))) + fractions.Fraction(1, mult((a[0], a[3], a[4], a[6], a[8]))) + fractions.Fraction(1, mult((a[0], a[3], a[4], a[7], a[8]))) + fractions.Fraction(1, mult((a[0], a[3], a[5], a[6], a[8]))) + fractions.Fraction(1, mult((a[0], a[3], a[5], a[7], a[8]))) + fractions.Fraction(1, mult((a[0], a[3], a[6], a[7], a[8]))) + fractions.Fraction(1, mult((a[0], a[4], a[5], a[6], a[8]))) + fractions.Fraction(1, mult((a[0], a[4], a[5], a[7], a[8]))) + fractions.Fraction(1, mult((a[0], a[4], a[6], a[7], a[8]))) + fractions.Fraction(1, mult((a[0], a[5], a[6], a[7], a[8]))) + fractions.Fraction(1, mult((a[1], a[2], a[3], a[4], a[8]))) + fractions.Fraction(1, mult((a[1], a[2], a[3], a[5], a[8]))) + fractions.Fraction(1, mult((a[1], a[2], a[3], a[6], a[8]))) + fractions.Fraction(1, mult((a[1], a[2], a[3], a[7], a[8]))) + fractions.Fraction(1, mult((a[1], a[2], a[4], a[5], a[8]))) + fractions.Fraction(1, mult((a[1], a[2], a[4], a[6], a[8]))) + fractions.Fraction(1, mult((a[1], a[2], a[4], a[7], a[8]))) + fractions.Fraction(1, mult((a[1], a[2], a[5], a[6], a[8]))) + fractions.Fraction(1, mult((a[1], a[2], a[5], a[7], a[8]))) + fractions.Fraction(1, mult((a[1], a[2], a[6], a[7], a[8]))) + fractions.Fraction(1, mult((a[1], a[3], a[4], a[5], a[8]))) + fractions.Fraction(1, mult((a[1], a[3], a[4], a[6], a[8]))) + fractions.Fraction(1, mult((a[1], a[3], a[4], a[7], a[8]))) + fractions.Fraction(1, mult((a[1], a[3], a[5], a[6], a[8]))) + fractions.Fraction(1, mult((a[1], a[3], a[5], a[7], a[8]))) + fractions.Fraction(1, mult((a[1], a[3], a[6], a[7], a[8]))) + fractions.Fraction(1, mult((a[1], a[4], a[5], a[6], a[8]))) + fractions.Fraction(1, mult((a[1], a[4], a[5], a[7], a[8]))) + fractions.Fraction(1, mult((a[1], a[4], a[6], a[7], a[8]))) + fractions.Fraction(1, mult((a[1], a[5], a[6], a[7], a[8]))) + fractions.Fraction(1, mult((a[2], a[3], a[4], a[5], a[8]))) + fractions.Fraction(1, mult((a[2], a[3], a[4], a[6], a[8]))) + fractions.Fraction(1, mult((a[2], a[3], a[4], a[7], a[8]))) + fractions.Fraction(1, mult((a[2], a[3], a[5], a[6], a[8]))) + fractions.Fraction(1, mult((a[2], a[3], a[5], a[7], a[8]))) + fractions.Fraction(1, mult((a[2], a[3], a[6], a[7], a[8]))) + fractions.Fraction(1, mult((a[2], a[4], a[5], a[6], a[8]))) + fractions.Fraction(1, mult((a[2], a[4], a[5], a[7], a[8]))) + fractions.Fraction(1, mult((a[2], a[4], a[6], a[7], a[8]))) + fractions.Fraction(1, mult((a[2], a[5], a[6], a[7], a[8]))) + fractions.Fraction(1, mult((a[3], a[4], a[5], a[6], a[8]))) + fractions.Fraction(1, mult((a[3], a[4], a[5], a[7], a[8]))) + fractions.Fraction(1, mult((a[3], a[4], a[6], a[7], a[8]))) + fractions.Fraction(1, mult((a[3], a[5], a[6], a[7], a[8]))) + fractions.Fraction(1, mult((a[4], a[5], a[6], a[7], a[8]))) - fractions.Fraction(1, mult((a[0], a[1], a[2], a[3], a[4], a[8]))) - fractions.Fraction(1, mult((a[0], a[1], a[2], a[3], a[5], a[8]))) - fractions.Fraction(1, mult((a[0], a[1], a[2], a[3], a[6], a[8])))
		frac += fractions.Fraction(-1, mult((a[0], a[1], a[2], a[3], a[7], a[8]))) - fractions.Fraction(1, mult((a[0], a[1], a[2], a[4], a[5], a[8]))) - fractions.Fraction(1, mult((a[0], a[1], a[2], a[4], a[6], a[8]))) - fractions.Fraction(1, mult((a[0], a[1], a[2], a[4], a[7], a[8]))) - fractions.Fraction(1, mult((a[0], a[1], a[2], a[5], a[6], a[8]))) - fractions.Fraction(1, mult((a[0], a[1], a[2], a[5], a[7], a[8]))) - fractions.Fraction(1, mult((a[0], a[1], a[2], a[6], a[7], a[8]))) - fractions.Fraction(1, mult((a[0], a[1], a[3], a[4], a[5], a[8]))) - fractions.Fraction(1, mult((a[0], a[1], a[3], a[4], a[6], a[8]))) - fractions.Fraction(1, mult((a[0], a[1], a[3], a[4], a[7], a[8]))) - fractions.Fraction(1, mult((a[0], a[1], a[3], a[5], a[6], a[8]))) - fractions.Fraction(1, mult((a[0], a[1], a[3], a[5], a[7], a[8]))) - fractions.Fraction(1, mult((a[0], a[1], a[3], a[6], a[7], a[8]))) - fractions.Fraction(1, mult((a[0], a[1], a[4], a[5], a[6], a[8]))) - fractions.Fraction(1, mult((a[0], a[1], a[4], a[5], a[7], a[8]))) - fractions.Fraction(1, mult((a[0], a[1], a[4], a[6], a[7], a[8]))) - fractions.Fraction(1, mult((a[0], a[1], a[5], a[6], a[7], a[8]))) - fractions.Fraction(1, mult((a[0], a[2], a[3], a[4], a[5], a[8]))) - fractions.Fraction(1, mult((a[0], a[2], a[3], a[4], a[6], a[8]))) - fractions.Fraction(1, mult((a[0], a[2], a[3], a[4], a[7], a[8]))) - fractions.Fraction(1, mult((a[0], a[2], a[3], a[5], a[6], a[8]))) - fractions.Fraction(1, mult((a[0], a[2], a[3], a[5], a[7], a[8]))) - fractions.Fraction(1, mult((a[0], a[2], a[3], a[6], a[7], a[8]))) - fractions.Fraction(1, mult((a[0], a[2], a[4], a[5], a[6], a[8]))) - fractions.Fraction(1, mult((a[0], a[2], a[4], a[5], a[7], a[8]))) - fractions.Fraction(1, mult((a[0], a[2], a[4], a[6], a[7], a[8]))) - fractions.Fraction(1, mult((a[0], a[2], a[5], a[6], a[7], a[8]))) - fractions.Fraction(1, mult((a[0], a[3], a[4], a[5], a[6], a[8]))) - fractions.Fraction(1, mult((a[0], a[3], a[4], a[5], a[7], a[8]))) - fractions.Fraction(1, mult((a[0], a[3], a[4], a[6], a[7], a[8]))) - fractions.Fraction(1, mult((a[0], a[3], a[5], a[6], a[7], a[8]))) - fractions.Fraction(1, mult((a[0], a[4], a[5], a[6], a[7], a[8]))) - fractions.Fraction(1, mult((a[1], a[2], a[3], a[4], a[5], a[8]))) - fractions.Fraction(1, mult((a[1], a[2], a[3], a[4], a[6], a[8]))) - fractions.Fraction(1, mult((a[1], a[2], a[3], a[4], a[7], a[8]))) - fractions.Fraction(1, mult((a[1], a[2], a[3], a[5], a[6], a[8]))) - fractions.Fraction(1, mult((a[1], a[2], a[3], a[5], a[7], a[8]))) - fractions.Fraction(1, mult((a[1], a[2], a[3], a[6], a[7], a[8]))) - fractions.Fraction(1, mult((a[1], a[2], a[4], a[5], a[6], a[8]))) - fractions.Fraction(1, mult((a[1], a[2], a[4], a[5], a[7], a[8]))) - fractions.Fraction(1, mult((a[1], a[2], a[4], a[6], a[7], a[8]))) - fractions.Fraction(1, mult((a[1], a[2], a[5], a[6], a[7], a[8]))) - fractions.Fraction(1, mult((a[1], a[3], a[4], a[5], a[6], a[8]))) - fractions.Fraction(1, mult((a[1], a[3], a[4], a[5], a[7], a[8]))) - fractions.Fraction(1, mult((a[1], a[3], a[4], a[6], a[7], a[8]))) - fractions.Fraction(1, mult((a[1], a[3], a[5], a[6], a[7], a[8]))) - fractions.Fraction(1, mult((a[1], a[4], a[5], a[6], a[7], a[8]))) - fractions.Fraction(1, mult((a[2], a[3], a[4], a[5], a[6], a[8]))) - fractions.Fraction(1, mult((a[2], a[3], a[4], a[5], a[7], a[8]))) - fractions.Fraction(1, mult((a[2], a[3], a[4], a[6], a[7], a[8]))) - fractions.Fraction(1, mult((a[2], a[3], a[5], a[6], a[7], a[8]))) - fractions.Fraction(1, mult((a[2], a[4], a[5], a[6], a[7], a[8]))) - fractions.Fraction(1, mult((a[3], a[4], a[5], a[6], a[7], a[8]))) + fractions.Fraction(1, mult((a[0], a[1], a[2], a[3], a[4], a[5], a[8]))) + fractions.Fraction(1, mult((a[0], a[1], a[2], a[3], a[4], a[6], a[8]))) + fractions.Fraction(1, mult((a[0], a[1], a[2], a[3], a[4], a[7], a[8]))) + fractions.Fraction(1, mult((a[0], a[1], a[2], a[3], a[5], a[6], a[8]))) + fractions.Fraction(1, mult((a[0], a[1], a[2], a[3], a[5], a[7], a[8]))) + fractions.Fraction(1, mult((a[0], a[1], a[2], a[3], a[6], a[7], a[8]))) + fractions.Fraction(1, mult((a[0], a[1], a[2], a[4], a[5], a[6], a[8]))) + fractions.Fraction(1, mult((a[0], a[1], a[2], a[4], a[5], a[7], a[8]))) + fractions.Fraction(1, mult((a[0], a[1], a[2], a[4], a[6], a[7], a[8]))) + fractions.Fraction(1, mult((a[0], a[1], a[2], a[5], a[6], a[7], a[8]))) + fractions.Fraction(1, mult((a[0], a[1], a[3], a[4], a[5], a[6], a[8]))) + fractions.Fraction(1, mult((a[0], a[1], a[3], a[4], a[5], a[7], a[8]))) + fractions.Fraction(1, mult((a[0], a[1], a[3], a[4], a[6], a[7], a[8]))) + fractions.Fraction(1, mult((a[0], a[1], a[3], a[5], a[6], a[7], a[8]))) + fractions.Fraction(1, mult((a[0], a[1], a[4], a[5], a[6], a[7], a[8]))) + fractions.Fraction(1, mult((a[0], a[2], a[3], a[4], a[5], a[6], a[8]))) + fractions.Fraction(1, mult((a[0], a[2], a[3], a[4], a[5], a[7], a[8]))) + fractions.Fraction(1, mult((a[0], a[2], a[3], a[4], a[6], a[7], a[8]))) + fractions.Fraction(1, mult((a[0], a[2], a[3], a[5], a[6], a[7], a[8]))) + fractions.Fraction(1, mult((a[0], a[2], a[4], a[5], a[6], a[7], a[8]))) + fractions.Fraction(1, mult((a[0], a[3], a[4], a[5], a[6], a[7], a[8]))) + fractions.Fraction(1, mult((a[1], a[2], a[3], a[4], a[5], a[6], a[8]))) + fractions.Fraction(1, mult((a[1], a[2], a[3], a[4], a[5], a[7], a[8]))) + fractions.Fraction(1, mult((a[1], a[2], a[3], a[4], a[6], a[7], a[8]))) + fractions.Fraction(1, mult((a[1], a[2], a[3], a[5], a[6], a[7], a[8]))) + fractions.Fraction(1, mult((a[1], a[2], a[4], a[5], a[6], a[7], a[8]))) + fractions.Fraction(1, mult((a[1], a[3], a[4], a[5], a[6], a[7], a[8]))) + fractions.Fraction(1, mult((a[2], a[3], a[4], a[5], a[6], a[7], a[8]))) - fractions.Fraction(1, mult((a[0], a[1], a[2], a[3], a[4], a[5], a[6], a[8]))) - fractions.Fraction(1, mult((a[0], a[1], a[2], a[3], a[4], a[5], a[7], a[8]))) - fractions.Fraction(1, mult((a[0], a[1], a[2], a[3], a[4], a[6], a[7], a[8]))) - fractions.Fraction(1, mult((a[0], a[1], a[2], a[3], a[5], a[6], a[7], a[8]))) - fractions.Fraction(1, mult((a[0], a[1], a[2], a[4], a[5], a[6], a[7], a[8]))) - fractions.Fraction(1, mult((a[0], a[1], a[3], a[4], a[5], a[6], a[7], a[8]))) - fractions.Fraction(1, mult((a[0], a[2], a[3], a[4], a[5], a[6], a[7], a[8]))) - fractions.Fraction(1, mult((a[1], a[2], a[3], a[4], a[5], a[6], a[7], a[8]))) + fractions.Fraction(1, mult(a[0:9]))
		if bcheckmax and frac > max_sum:
			return fractions.Fraction(1, 1)
	return frac


bln_count = False
hsh_count_all = {}
hsh_count_prime = {}

#calc_density1(720, [5, 9, 16])
#[(density.numerator, density.denominator) for density in [seq.calc_density1(536870915, f1) for f1 in seq.factorizations_outer(536870915, bln_remove_gt_half=False)]]
def calc_density1(i, a):
	global verbose
	global bln_count
	global bln_cpp
	global bln_numba
	global save_memory
	global max_sum
	global total_calc_density
	global aryprimes
	if verbose: print(f"calc_density1(i={i}, a={a}), bln_count={bln_count}, bln_numba={bln_numba}")
	if not save_memory and i > len(aryprimes):
		aryprimes = fill_primes(i + 2)
	if bln_count:
		global hsh_count_all
		global hsh_count_prime
		if len(a) in hsh_count_all:
			hsh_count_all[len(a)] += 1
		else:
			hsh_count_all[len(a)] = 1
		is_prime = True
		for i in range(0, len(a)):
			if save_memory and bln_cpp:
				if not divisors.is_prime(a[i]):
					is_prime = False
			elif not aryprimes[a[i]]:
				is_prime = False
		if is_prime:
			if len(a) in hsh_count_prime:
				hsh_count_prime[len(a)] += 1
			else:
				hsh_count_prime[len(a)] = 1
	tcalc = time.time()
	if bln_cpp:
		#max_sum = divisors.BoostRational(1, 2)
		#(max_sum.numerator, max_sum.denominator)
		#frac1 = divisors.calc_density_unrolled(1908480, [3, 5, 28, 64, 71], max_sum)
		#dir(frac1)
		#tuples = [(f1, divisors.calc_density_unrolled(1908480, f1, max_sum)) for f1 in seq.factorizations_outer(1908480, bln_remove_gt_half=False)]
		#[tpl for tpl in tuples if tpl[1].denominator <= 16]
		#[tpl for tpl in tuples if tpl[1] >= BoostRational(3, 32)]
		frac1 = divisors.calc_density_unrolled(i, a, max_sum)
	elif bln_numba:
		frac1 = calc_density_numba(i, a, max_sum)
	else:
		frac1 = calc_density_python(i, a, max_sum)
	total_calc_density += (time.time() - tcalc)
	return frac1


spec = [
	('size', numba.int64),
	('keys_capacity', numba.int64),
	('values_capacity', numba.int64),
	('keys_index', numba.int64),
	('values_index', numba.int64),
	('resizeable', numba.bool_),
	('keys', numba.int64[:]),
	('values', numba.int64[:]),
]

@numba.experimental.jitclass(spec)
class ArrayArray:
	def __init__(self, capacity, resizeable):
		self.size = 0
		self.keys_capacity = capacity
		self.values_capacity = 2*capacity
		self.keys_index = 0
		self.values_index = 0
		self.resizeable = resizeable
		self.keys = numpy.zeros(self.keys_capacity, dtype=numpy.int64)
		self.values = numpy.zeros(self.values_capacity, dtype=numpy.int64)
	
	def append(self, ary):
		if self.resizeable and self.values_index + len(ary) >= self.values_capacity:
			self.values_capacity += 2048
			temp = numpy.zeros(self.values_capacity, dtype=numpy.int64)
			temp[:self.values_index] = self.values[:self.values_index]
			self.values = temp
		i = self.values_index
		for a in ary:
			self.values[self.values_index] = a
			self.values_index += 1
		j = self.values_index - 1
		if self.resizeable and self.keys_index + len(ary) >= self.keys_capacity:
			self.keys_capacity += 2048
			temp = numpy.zeros(self.keys_capacity, dtype=numpy.int64)
			temp[:self.keys_index] = self.keys[:self.keys_index]
			self.keys = temp
		self.keys[self.keys_index] = i
		self.keys[self.keys_index + 1] = j
		self.keys_index += 2
	
	def removeAt(self, idx):
		self.keys[2*idx] = -1
		self.keys[2*idx + 1] = -1
	
	def __len__(self):
		return self.keys_index//2
	
	def __getitem__(self, idx):
		ary = numba.typed.List.empty_list(item_type=numpy.int64)
		idx = 2*idx
		if idx < 0 or idx >= self.keys_index:
			return ary
		i = self.keys[idx]
		j = self.keys[idx + 1]
		if i == -1 or j == -1:
			return ary
		ary.append(self.values[i])
		i += 1
		while i <= j:
			ary.append(self.values[i])
			i += 1
		return ary
	
	def to_list(self):
		return self.to_array()
	
	def to_array(self):
		return [self.values[self.keys[idx]:self.keys[idx+1]+1] for idx in range(0, self.keys_index, 2) if self.keys[idx] >= 0 and self.keys[idx+1] >= 0]

def to_array(aa):
	return [aa.values[aa.keys[idx]:aa.keys[idx+1]+1] for idx in range(0, aa.keys_index, 2) if aa.keys[idx] >= 0 and aa.keys[idx+1] >= 0]



#div = Divisors(aryprimes)
#div = divisors.Divisors.get_instance()
#divisors.set_verbose(False)

#@numba.jit(nopython=True)
def backtrack_divisors(n, target, factors, combinations, div):
	global min_factors
	global max_factors
	if target == 1:
		if len(factors) >= min_factors + 1 and len(factors) <= max_factors + 1 and factors[1] != n:
			bappend = True
			for j in range(len(factors) - 1, 1, -1):
				for k in range(j - 1, 0, -1):
					if factors[j] % factors[k] == 0:
						bappend = False
						break
				if not bappend:
					break
			if bappend:
				combinations.append(sorted(factors[1:]))
		return
	#for i in sympy.divisors(target)[1:]:
	for i in divisors.divisors(target)[1:]:
		if len(factors) == 1 or (len(factors) <= max_factors and i > factors[-1]):
			factors.append(i)
			backtrack_divisors(n, target // i, factors, combinations, div)
			factors.pop() 

#s = set(tuple(t) for t in [[4, 18, 22, 27, 77], [4, 18, 22, 33, 63], [6, 8, 9, 21, 363], [6, 8, 21, 27, 121], [6, 8, 21, 3267], [6, 8, 27, 33, 77], [6, 8, 27, 2541], [6, 8, 63, 1089], [6, 8, 77, 891], [6, 8, 81, 847], [6, 8, 121, 567], [6, 8, 189, 363], [6, 8, 231, 297], [27, 36, 44, 77], [48, 63, 1089], [48, 77, 891], [48, 81, 847], [48, 121, 567], [48, 189, 363], [48, 231, 297]])			

"""
factors = [1,]
combinations = sequence.ArrayArray(1024, True)
backtrack_sympy_divisors(3293136, 3293136, factors, combinations)
sequence.backtrack_sympy_divisors(3293136, 3293136, factors, combinations)
"""
def backtrack_sympy_divisors(n, target, factors, combinations):
	global min_factors
	global max_factors
	if target == 1:
		if len(factors) >= min_factors + 1 and len(factors) <= max_factors + 1 and factors[1] != n:
			bappend = True
			for j in range(len(factors) - 1, 1, -1):
				for k in range(j - 1, 0, -1):
					if factors[j] % factors[k] == 0:
						bappend = False
						break
				if not bappend:
					break
			if bappend:
				#if tuple(sorted(factors[1:])) in s:
				#	print(f"backtrack_sympy_divisors({n}, {target}, {factors}, combinations)")
				combinations.append(sorted(factors[1:]))
		return
	for i in sympy.divisors(target)[1:]:
		if len(factors) == 1 or (len(factors) <= max_factors and i > factors[-1]):
			factors.append(i)
			backtrack_sympy_divisors(n, target // i, factors, combinations)
			factors.pop() 


bln_backtrack_init = False
hsh_arrayarray = {}

#factors = [1,]
#combinations = ArrayArray(2048, True)
#sequence_th.backtrack_divisors(3293136, 3293136, factors, combinations)
#combinations = sequence_th.ArrayArray(1024, True)
#combinations.append([2, 3])
#sequence_th.factorCombinations(3293136).to_array()
#@memory_profiler.profile
def factorCombinations(n2, thread_local):
	global verbose
	global bln_cpp
	global bln_backtrack_init
	global total_factor_combinations
	global div
	if verbose: print(f"factorCombinations({n2})")
	tfactor = time.time()
	n = n2
	if not bln_cpp and not bln_backtrack_init:
		factors = [1,]
		combinations = ArrayArray(2, True)
		if bln_divisors:
			backtrack_divisors(1, 1, factors, combinations, div)
		else:
			backtrack_numba(1, 1, factors, combinations, small_factor_cache, factor_cache)
		bln_backtrack_init = True
	#factors = numba.typed.List.empty_list(item_type=numpy.int64)
	#combinations = []
	factors = [1,]
	combinations = ArrayArray(2048, True)
	if bln_cpp:
		combinations = divisors.Combinations(n, thread_local)
		combinations.backtrack(n2)
		#combinations = combinations.get_arrayarray()
	elif bln_numba:
		backtrack_numba(n, n2, factors, combinations, small_factor_cache, factor_cache)
	elif bln_divisors:
		backtrack_divisors(n, n2, factors, combinations, div)
	total_factor_combinations += (time.time() - tfactor)
	if bln_count:
		key = (combinations.keys_capacity, combinations.values_capacity)
		if key in hsh_arrayarray:
			hsh_arrayarray[key] += 1
		else:
			hsh_arrayarray[key] = 1
	return combinations


#ary_tpl = sequence_th.factorCombinations(3293136)
#[ary_tpl[at] for at in range(0, len(ary_tpl))]
#sequence_th.to_array(sequence_th.factorizations_outer(3293136))
#frozenset([tuple(ary) for ary in sequence_th.factorizations_outer(3293136, bln_remove_gt_half=False).to_array()])
#sequence.factorizations_outer(3293136)
#@memory_profiler.profile
def factorizations_outer(n, thread_local, bln_remove_gt_half=True):
	global min_factors
	global max_factors
	global verbose
	global total_factorizations_outer
	if verbose: print(f"factorizations_outer({n})")
	return factorCombinations(n, thread_local)
	ary_tpl = factorCombinations(n, thread_local)
	tfactorizations = time.time()
	at = -1
	while at < len(ary_tpl) - 1:
		at += 1
		if len(ary_tpl[at]) < min_factors or len(ary_tpl[at]) > max_factors:
			if verbose: print(f"removing ary_tpl[{at}] = {ary_tpl[at]}")
			#ary_tpl.remove(ary_tpl[at])
			ary_tpl.removeAt(at)
			# at -= 1
			continue
		#ary_tpl[at] = sorted(ary_tpl[at])
		if bln_remove_gt_half and 1/ary_tpl[at][0] + 1/ary_tpl[at][1] - 1/mult(tuple(ary_tpl[at][0:2])) + 1/ary_tpl[at][2] - 1/mult(tuple(ary_tpl[at][1:3])) - 1/mult((ary_tpl[at][0], ary_tpl[at][2])) + 1/mult(tuple(ary_tpl[at][0:3])) > 0.5:
			if verbose: print(f"removing ary_tpl[{at}] = {ary_tpl[at]}")
			# print(f"removed {ary_tpl[at]} at line 151")
			#ary_tpl.remove(ary_tpl[at])
			ary_tpl.removeAt(at)
			# at -= 1
			continue
		if False and 1/ary_tpl[at][0] + 1/ary_tpl[at][1] - 1/mult(tuple(ary_tpl[at][0:2])) > 0.5:
			if verbose: print(f"removing ary_tpl[{at}] = {ary_tpl[at]}")
			#ary_tpl.remove(ary_tpl[at])
			ary_tpl.removeAt(at)
			# at -= 1
			continue
		if False and ary_tpl[at][0] >= 9:
			if verbose: print(f"removing ary_tpl[{at}] = {ary_tpl[at]}")
			#ary_tpl.remove(ary_tpl[at])
			ary_tpl.removeAt(at)
			# at -= 1
			continue
		prev_t = ary_tpl[at][0]
		for this_t in ary_tpl[at][1:]:
			if this_t == prev_t:
				if verbose: print(f"removing ary_tpl[{at}] = {ary_tpl[at]}")
				#ary_tpl.remove(ary_tpl[at]) 
				ary_tpl.removeAt(at)
				#at -= 1
				break
			prev_t = this_t
	total_factorizations_outer += (time.time() - tfactorizations)
	if verbose: print(f"factorizations_outer({n}) returning len(ary_tpl) = {len(ary_tpl)}")
	return ary_tpl

arydivisorsids = []
arythreadids = []

#@memory_profiler.profile
def factors_loop(ifinish, th, thread_local, q_in, q_out, q_thread_max, istepby, bbreak):
	global verbose
	global arydivisorsids
	global arythreadids
	global istarted
	global keyboard_interrupt_event
	global bln_cpp
	global bln_numba
	global save_memory
	global bln_factors_loop
	global setfractions
	global max_sum
	global total_calc_density
	istarted += 1
	aryprimes = fill_primes(ifinish)
	ilen = len(aryprimes)
	div = divisors.get_instance(ifinish, thread_local)
	isize = div.size()
	arydivisorsids.append(div.id())
	arythreadids.append(div.thread_id()[0])
	if verbose:
		print(f"factors_loop() th = {th}")
		print(f"current_thread().name = {threading.current_thread().name}")
		print(f"get_ident() = {threading.get_ident()}")
		print(f"get_native_id() = {threading.get_native_id()}")
		print(f"div.id() = {div.id()}")
		print(f"divisors.id() = {divisors.id()}")
		print(f"div.thread_id() = {div.thread_id()}")
		print(f"divisors.thread_id() = {divisors.thread_id()}")
	hshfractions = [hash((frac.numerator, frac.denominator)) for frac in setfractions]
	max_sum = divisors.BoostRational(1, 1) if bln_cpp else Fraction(1, 1) if bln_numba else fractions.Fraction(1, 1)
	bstarted = False
	bln_factors_loop = True
	while bln_factors_loop and not keyboard_interrupt_event.is_set():
		tpl = q_in.get()
		if tpl is None:
			q_out.put(None)
			q_in.task_done()
			break
		#if False and ((tpl[0] <= 39443712 and tpl[1] >= 39443712) or (tpl[0] <= 39621120 and tpl[1] >= 39621120)):
		#	verbose = True
		#else:
		#	verbose = False
		if verbose: 
			print(f"factors_loop() th = {th}, tpl = {tpl}, istepby = {istepby}")
			print(f"factors_loop() setfractions = {[str(x.numerator) + "/" + str(x.denominator) for x in list(setfractions)]}")
		if not bstarted:
			bstarted = True
		if not save_memory and tpl[1] > ilen:
			aryprimes = fill_primes(tpl[1] + 2)
			ilen = len(aryprimes)
		if tpl[1] > isize:
			isize = div.resize(tpl[1])
			if tpl[1] > isize:
				print(f"factors_loop() this code not valid for ifinish > {isize:,} ifinish={tpl[1]:,} (2**{round(math.log(tpl[1], 2), 2):.2f})")
				q_out.put(None)
				q_in.task_done()
				break
		for i in range(tpl[0], tpl[1], istepby):
			if save_memory and bln_cpp:
				if div.is_prime(i) or (i % 2 == 0 and div.is_prime[i//2]) or (i % 3 == 0 and div.is_primes[i//3]):
					continue
			elif aryprimes[i] or (i % 2 == 0 and aryprimes[i//2]) or (i % 3 == 0 and aryprimes[i//3]):
				continue
			#verbose = i in [39443712, 39621120]
			fact2 = []
			#import sys
			#sys.path.append("E:\\Python\\Sequence")
			#import sequence_th as seq
			#i = 14880
			#[(density.numerator, density.denominator) for density in [seq.calc_density1(i, f1) for f1 in seq.factorizations_outer(i, bln_remove_gt_half=False)]]
			for f1 in factorizations_outer(i, thread_local, bln_remove_gt_half=False):
				if verbose: print(f"factors_loop() i = {i}, f1 = {f1}")
				if bln_cpp:
					tcalc = time.time()
					frac1 = div.calc_density_unrolled(i, f1, max_sum)
					total_calc_density += (time.time() - tcalc)
				else:
					frac1 = calc_density1(i, f1)
				frac1hash = hash((frac1.numerator, frac1.denominator))
				#print(f"calc_density1({i}, {f1}) i: {type(i)}, f1: {[type(x) for x in f1]}")
				#print(f"calc_density1({i}, {f1}) frac1.num: {type(frac1.numerator)}, frac1.den: {type(frac1.denominator)}")
				if verbose: 
					print(f"factors_loop() i = {i}, frac1 = {frac1}, hash(frac1) = {frac1hash}, hshfractions = {hshfractions}")
					print(f"factors_loop() denominator = {frac1.denominator}")
					print(f"factors_loop() f1 = {[int(x) for x in f1]}")
					print(f"factors_loop() ({frac1hash} in hshfractions) ? {frac1hash in hshfractions}")
				if frac1hash in hshfractions:
					#bln = False
					#for frac2 in setfractions:
					#	if frac1.denominator == frac2.denominator and frac1.numerator == frac2.numerator:
					#		bln = True
					#if bln:
					fact2.append((frac1.denominator, frac1, i, [int(x) for x in f1]))
					if verbose: print(f"factors_loop() fact2[-1] = {fact2[-1]}")
					if bbreak:
						break
			if len(fact2) > 0:
				fact2 = sorted(fact2)
				q_out.put(fact2)
				if verbose:
					for f2 in fact2:
						print(f"factors_loop() {f2[1]}\t\t{f2[2]:,}\t\t{f2[3]}\t\t{len(f2[3])}")
		try:
			q_in.task_done()
		except ValueError as ve:
			if verbose: print(f"factors_loop() ValueError = {ve}")
			pass
		q_thread_max.put((th, tpl[1]-1))


def print_rows():
	global directory
	conn = sqlite3.connect(f"{directory}\\sequence.bin", check_same_thread=False)
	curs = conn.cursor()
	# _ = curs.execute("SELECT COUNT(*) FROM sequence")
	# curs.fetchone()
	_ = curs.execute("SELECT num, den, ord, ary, len FROM sequence WHERE ord >= 65520 ORDER BY ord")
	for row in curs.fetchall():
		print(row)
	conn.close()


"""
import sqlite3
conn = sqlite3.connect(f"{directory}\\sequence.bin", check_same_thread=False)
curs = conn.cursor()
_ = curs.execute("SELECT DISTINCT ord FROM sequence WHERE ord > (SELECT max(ord)-32 FROM sequence) LIMIT 32")
curs.fetchall()
_ = curs.execute("CREATE TABLE sequence (seq_id INTEGER PRIMARY KEY AUTOINCREMENT, num INTEGER, den INTEGER, ord INTEGER, len INTEGER)")
_ = curs.execute("CREATE TABLE array (ary_id INTEGER PRIMARY KEY AUTOINCREMENT, seq_id INTEGER, a INTEGER)")
_ = curs.execute("CREATE INDEX idx_sequence_ord ON sequence (ord)")
_ = curs.execute("CREATE INDEX idx_sequence_den_num ON sequence (den, num)")
_ = curs.execute("CREATE INDEX idx_sequence_len ON sequence (len)")
_ = curs.execute("CREATE INDEX idx_array_seq ON array (seq_id)")
conn.commit()
conn.close()
t0, i0, i1, i2
"""
def all_factors_loop(ifinish, th, thread_local, q_in, q_out, q_thread_max, istepby):
	global verbose
	global max_denominator
	global istarted
	global bln_cpp
	global bln_numba
	global save_memory
	global keyboard_interrupt_event
	global bln_all_factors_loop
	div = divisors.get_instance(ifinish, thread_local)
	isize = div.size()
	bstarted = False
	bln_all_factors_loop = True
	while bln_all_factors_loop and not keyboard_interrupt_event.is_set():
		tpl = q_in.get()
		if verbose: print(f"all_factors_loop() tpl = {tpl}")
		if not bstarted:
			bstarted = True
			istarted += 1
		if tpl is None:
			q_out.put(None)
			q_in.task_done()
			break
		if verbose:
			print("# ")
			print("# ")
			print(f"# all_factors_loop({tpl[0]}, {tpl[1]})")
			print("# ")
			print("# ")
		if not save_memory and tpl[1] > len(aryprimes) and tpl[1] <= isize:
			aryprimes = fill_primes(tpl[1] + 2)
		for i in range(tpl[0], tpl[1], istepby):
			if save_memory and bln_cpp:
				if div.is_prime(i):
					if i <= max_denominator:
						q_out.put([(i, Fraction(1, i), i, [i,])])
					continue
			elif aryprimes[i]:
				if i <= max_denominator:
					q_out.put([(i, Fraction(1, i), i, [i,])])
				continue
			#fact1 = frozenset([tuple(ary) for ary in factorizations_outer(i, bln_remove_gt_half=False).to_array()])
			fact2 = []
			if verbose: print(f"all_factors_loop() i = {i}")
			for f1 in factorizations_outer(i, thread_local, bln_remove_gt_half=False):
				if verbose: print(f"all_factors_loop() i = {i}, f1 = {f1}")
				frac1 = calc_density1(i, f1)
				if verbose: print(f"all_factors_loop() i = {i}, frac1 = {frac1}")
				if frac1.denominator <= max_denominator:
					fact2.append((frac1.denominator, frac1, i, [int(x) for x in f1]))
			if len(fact2) > 0:
				fact2 = sorted(fact2)
				q_out.put(fact2)
				if verbose:
					for f2 in fact2:
						print(f"all_factors_loop() {f2[1]}\t\t{f2[2]:,}\t\t{f2[3]}\t\t{len(f2[3])}")
			if verbose: print(f"all_factors_loop() i = {i}, lineno = {sys._getframe(0).f_lineno}")
		try:
			q_in.task_done()
		except ValueError as ve:
			pass
		if verbose: print(f"all_factors_loop() i = {i}, lineno = {sys._getframe(0).f_lineno}")
		q_thread_max.put((th, tpl[1]-1))

# sequence_th.ary_factors_loop([3293136,])
# [sequence_th.calc_density(3293136, ary) for ary in sequence.factorizations_outer(3293136, bln_remove_gt_half=False).to_array()]
def ary_factors_loop(ary, thread_local):
	global aryprimes
	div = divisors.get_instance(max(ary), thread_local)
	for i in ary:
		if save_memory and bln_cpp:
			if div.is_prime(i):
				continue
		elif aryprimes[i]:
			continue
		fact1 = frozenset([tuple(ary) for ary in factorizations_outer(i, thread_local, bln_remove_gt_half=False).to_array()])
		fact2 = []
		for f1 in fact1:
			frac1 = calc_density1(i, f1)
			if frac1.numerator == 1 or frac1.denominator <= 32:
				fact2.append((frac1.denominator, frac1, i, list(f1)))
		for f2 in sorted(fact2):
			print(f"{f2[1]}\t\t{f2[2]:,}\t\t{f2[3]}\t\t{len(f2[3])}")


def check_factors(i, thread_local, print_true, print_false):
	global setfractions
	max_sum = 1
	fact1 = frozenset([tuple(ary) for ary in factorizations_outer(i, thread_local)])
	# (9, 12, 26, 235) in fact1
	blnfound = False
	for f1 in fact1:
		frac1 = calc_density1(i, f1, max_sum)
		if frac1 in setfractions:
			blnfound = True
			if print_true:
				print(f"{frac1} {i:,} {list(f1)}")
	if not blnfound and print_false:
		print(f"Not found! {i:,}")


hsh, minhshkeys, maxhshkeys = [], sys.maxsize, 0 # sys.maxsize = 2**63
bfile = True
bzip = False
bdata = False
directory = ""
filename = "sequence.txt"

def fill_hsh(i):
	global hsh
	global minhshkeys
	global maxhshkeys
	global lock
	global directory
	if not bdata:
		return
	with lock:
		if not os.path.exists(f"{directory}\\sequence.bin"):
			return
		conn = sqlite3.connect(f"{directory}\\sequence.bin")
		curs = conn.cursor()
		# curs.execute("PRAGMA busy_timeout = 5000;")
		_ = curs.execute("CREATE INDEX IF NOT EXISTS idx_ord ON sequence (ord)")
		if len(hsh) == 0 or i < minhshkeys:
			print(f"fill_hsh() len(hsh) = {len(hsh)}, fact2[0][2] = {i}, minhshkeys = {minhshkeys}")
			# 10068080
			# 10174560
			_ = curs.execute("SELECT MAX(ord) FROM sequence")
			row = curs.fetchone()
			print(f"MAX(ord) = {row[0]}")
			maxhshkeys = row[0]
			_ = curs.execute("SELECT ord, COUNT(*) FROM sequence WHERE ord >= ? GROUP BY ord ORDER BY ord", (i,))
			for row in curs.fetchall():
				if minhshkeys == sys.maxsize:
					minhshkeys = row[0]
					hsh = [0,] * (maxhshkeys - minhshkeys + 1)
				if row[1] >= 100:
					print(f"hsh[{row[0]}] = {row[1]}")
				hsh[row[0] - minhshkeys] = row[1]
			#minhshkeys = min(hsh.keys())
			#maxhshkeys = max(hsh.keys())
		_ = curs.execute("DROP INDEX IF EXISTS idx_ord")
		_ = curs.execute("DROP INDEX IF EXISTS idx_den_num")
		_ = curs.execute("DROP INDEX IF EXISTS idx_len")
		conn.execute("VACUUM")
		conn.commit()
		conn.close()


factscache = 72
linescache = 8
writescache = 2
#filebuffer = 32768
filebuffer = 8192
icompleted = 0

def writer(q_out, q_thread_max):
	global verbose
	global inumthreads
	global icompleted
	global lock
	global t0
	global hsh
	global minhshkeys
	global maxhshkeys
	global directory
	global filename
	global factscache
	global linescache
	global writescache
	global filebuffer
	
	global bfile
	global bzip
	global bdata
	global total_file
	global total_data
	
	global total_factor_combinations
	global total_factorizations_outer
	global total_calc_density
	global total_writer
	
	global keyboard_interrupt_event
	global bln_keyboard_interrupt
	global bln_writer
	bln_writer = True
	
	# fact2 = q_out.get(block=False)
	# if bdata:
	#	 fill_hsh(fact2[0][2])
	
	bverbose = verbose
	bfirst = True
	bfileclosed = False
	bdataclosed = False
	hsh = {}
	hshmax = {}
	conn, curs, facts, lines, data = None, None, [], [], []
	f_zip, f_buf, f_txt = None, None, None
	try:
		if bdata:
			conn = sqlite3.connect(f"{directory}\\sequence.bin")
			curs = conn.cursor()
			curs.execute("PRAGMA journal_mode = MEMORY;")
			curs.execute("PRAGMA temp_store = MEMORY;")
			# curs.execute("PRAGMA synchronous = OFF;")
			curs.execute("PRAGMA cache_size = 262144;")
			curs.execute("PRAGMA page_size = 16384;")
			conn.commit()
			curs.execute("BEGIN TRANSACTION;")
		if bfile:
			if bzip:				
				f_zip = gzip.open(os.path.join(directory, f"{filename}.gz"), mode="ab", compresslevel=7, encoding="ascii")
				f_buf = io.BufferedWriter(f_zip, buffer_size=filebuffer)
				f_txt = io.TextIOWrapper(f_buf, encoding='ascii')
			else:
				f_txt = open(os.path.join(directory, filename), "a", buffering=filebuffer)
		
		i0, i1, itotal, ifacts, ilines, iwrites, icompleted = 0, 0, 0, 0, 0, 0, 0
		if bverbose:
			print(f"writer() bverbose = {bverbose}, bfile = {bfile}, bzip = {bzip}, bdata = {bdata}")
			print(f"writer() factscache = {factscache}, linescache = {linescache}, writescache = {writescache}")
			print(f"writer() directory = {directory}, filename = {filename}")
			print(f"writer() inumthreads = {inumthreads}, icompleted = {icompleted}")
		while bln_writer and not keyboard_interrupt_event.is_set():
			if verbose: print(f"writer() bln_writer = {bln_writer}, icompleted = {icompleted}, keyboard_interrupt_event.is_set() = {keyboard_interrupt_event.is_set()}")
			fact2 = q_out.get(block=True)
			if verbose:
				print(f"fact2 = {fact2}")
				print(f"q_thread_max.empty() = {q_thread_max.empty()}")
				print(f"q_thread_max.qsize() = {q_thread_max.qsize()}")
			while not q_thread_max.empty():
				ith, imax = q_thread_max.get(block=False)
				hshmax[ith] = imax
				q_thread_max.task_done()
			if verbose and len(hshmax) > 0:
				print(f"hshmax[{ith}] = {hshmax[ith]}")
			twriter = time.time()
			if bfirst:
				bfirst = False				
				if bverbose: 
					if fact2:
						print(f"writer() bfile = {bfile}, bdata = {bdata}, len(fact2) = {len(fact2)}, fact2[0][2] = {fact2[0][2]}, icompleted = {icompleted}")
					else:
						print(f"writer() bfile = {bfile}, bdata = {bdata}, fact2 = None, icompleted = {icompleted}")
			if fact2 is None:
				icompleted += 1
				if icompleted >= inumthreads:
					#print(f"writer() icompleted = {icompleted}, inumthreads = {inumthreads}")
					dt = (time.time() - t0)/60
					total_writer += (time.time() - twriter)
					#print(f"{round(dt, 2)} minutes ~ {int(round((i1 - i0)/dt, 0)):,} per min")
					q_out.task_done()
					break
				else:
					if bverbose: print(f"writer() fact2 is None")
					q_out.task_done()
					continue
			if i0 == 0:
				#print(f"i0 = {i0}, fact2 = {fact2}")
				i0 = fact2[0][2]
			else:
				#print(f"i0 = {i0}, fact2 = {fact2}")
				i1 = fact2[0][2]
			if bdata:
				if fact2[0][2] <= maxhshkeys and fact2[0][2] >= minhshkeys and hsh[fact2[0][2] - minhshkeys] > 0:
					print(f"writer() {hsh[fact2[0][2] - minhshkeys]} row{'s' if hsh[fact2[0][2] - minhshkeys] > 1 else ''} found for ord = {fact2[0][2]:,}")
					continue
			itotal += len(fact2)
			ilines += len(fact2)
			ifacts += len(fact2)
			facts.extend(fact2)
			if bverbose: print(f"writer() ilines = {ilines}")
			iminmax = 0
			if len(hshmax) >= inumthreads:
				iminmax = min(hshmax.values())
			elif inumthreads == 1:
				iminmax = 2**53
			if verbose:
				print(f"writer() ifacts = {ifacts}")
				print(f"writer() len(hshmax) = {len(hshmax)}")
				print(f"writer() min(hshmax.values()) = {min(hshmax.values()) if len(hshmax) > 0 else 0}")
			for f2 in sorted([f2 for f2 in facts if f2[2] <= iminmax], key=lambda f2: f2[2]):
				if str(f2[1]) not in hsh:
					hsh[str(f2[1])] = [f2[2],]
				else:
					hsh[str(f2[1])].append(f2[2])
				print(f"{f2[1]}\t\t{f2[2]:,}\t\t{f2[3]}\t\t{len(f2[3])}")
				if bfile:
					lines.append(f"{f2[1]}\t{f2[2]:,}\t{f2[3]}\t{len(f2[3])}\n")
				if bdata:
					# data.append((f2[1].numerator, f2[1].denominator, f2[2], str(f2[3]), len(f2[3])))
					_ = curs.execute("INSERT INTO sequence (num, den, ord, len) VALUES (?, ?, ?, ?);", (f2[1].numerator, f2[1].denominator, f2[2], len(f2[3])))
					seq_id = curs.lastrowid
					_ = curs.executemany("INSERT INTO array (seq_id, a) VALUES (?, ?);", [(seq_id, x) for x in f2[3]])					
			ifacts = 0
			facts = [f2 for f2 in facts if f2[2] > iminmax]
			if ilines >= linescache:
				iwrites += 1
				if bverbose:
					print(f"ilines = {ilines}")
					print(f"len(lines) = {len(lines)}")
					print(f"iwrites = {iwrites}")
				with lock:
					# 0.16 seconds writing to file
					# 412.05 seconds writing to database
					if bfile:
						tfile = time.time()
						_ = f_txt.writelines(lines)
						if iwrites >= writescache:
							f_txt.flush()
						total_file += (time.time() - tfile)
						#print(f"{round(time.time() - tfile, 2)} seconds writing to file")
					if bdata:
						tdata = time.time()
						# f2 = (Fraction(1, 13), 64584, "[26, 36, 69]", 3)
						# _ = curs.executemany("INSERT INTO sequence (num, den, ord, len) VALUES (?, ?, ?, ?);", data)
						if iwrites >= writescache:
							curs.execute("COMMIT;")
							conn.commit()
							curs.execute("BEGIN TRANSACTION;")
						total_data += (time.time() - tdata)
						print(f"{round(time.time() - tdata, 2)} seconds writing to database")
				if iwrites >= writescache:
					iwrites = 0
				ilines = 0
				data = []
				lines = []
				dt = (time.time() - t0)/60
				total_writer += (time.time() - twriter)
				# 0.68 minutes writing to file
				# 0.35 minutes writing to database
				# 48.99 total minutes factorCombinations()
				# 38.98 total minutes factorizations_outer()
				# 129.62 total minutes calc_density()
				# 0.14 total minutes writing to file
				# 0.06 total minutes writing to database
				if bverbose:
					print(f"# {round(total_factor_combinations/60, 2)} total minutes factorCombinations()")
					print(f"# {round(total_factorizations_outer/60, 2)} total minutes factorizations_outer()")
					print(f"# {round(total_calc_density/60, 2)} total minutes calc_density()")
					print(f"# {round(total_writer/60, 2)} total minutes writer()")
					print(f"# {round(total_file, 2)} total seconds writing to file")
					print(f"# {round(total_data, 2)} total seconds writing to database")
					#print(f"# i0 = {i0}")
					#print(f"# i1 = {i1}")
					#print(f"# i1 - i0 = {i1 - i0}")
					#print(f"# itotal = {itotal} ~ {round(itotal/dt, 1):.1f} per min")
					print(f"# {round(dt, 2):.2f} mins ({round(dt/60, 2):.2f} hrs) ~ {int(round((i1 - i0)/dt, 0)):,} per min")
			else:
				total_writer += (time.time() - twriter)
			try:
				q_out.task_done()
			except ValueError as ve:
				pass
		if icompleted >= inumthreads:
			if len(facts) > 0:
				for f2 in sorted(facts, key=lambda x: x[2]):
					if str(f2[1]) not in hsh:
						hsh[str(f2[1])] = [f2[2],]
					else:
						hsh[str(f2[1])].append(f2[2])
					print(f"{f2[1]}\t\t{f2[2]:,}\t\t{f2[3]}\t\t{len(f2[3])}")
					s = f"{f2[1]}\t{f2[2]:,}\t{f2[3]}\t{len(f2[3])}\n"
					if s not in lines:
						lines.append(s)
				facts = []
			if len(hsh) > 0:
				for k, v in hsh.items():
					print(f"{k}\t{v}")
				hsh = {}
			with lock:
				if bfile:
					tfile = time.time()
					if bverbose:
						print(f"line = {sys._getframe(0).f_lineno}, ifact = {ifacts}")
						print(f"line = {sys._getframe(0).f_lineno}, len(facts) = {len(facts)}")
						print(f"line = {sys._getframe(0).f_lineno}, ilines = {ilines}")
						print(f"line = {sys._getframe(0).f_lineno}, len(lines) = {len(lines)}")
						print(f"line = {sys._getframe(0).f_lineno}, len(hsh) = {len(hsh)}")
					if len(lines) > 0:
						try:
							_ = f_txt.writelines(lines) 
						except FileNotFoundError as fnfe:
							print(traceback.format_exc())
							print(f"file is {directory}\\{filename}")
							print(f"len(lines) is {len(lines)}")
							pass
						ilines = 0
						lines = []
						ifacts = 0
						facts = []
					_ = f_txt.write("\n") 
					f_txt.flush()
					if not bzip:
						f_txt.close()
					else:
						f_txt.detach()
						f_zip.flush()
						f_zip.close()
					total_file += (time.time() - tfile)
					bfileclosed = True
				if bdata:
					if conn.in_transaction:
						curs.execute("COMMIT;")
					conn.commit()
					conn.close()
					bdataclosed = True
	except Exception as ex:
		#traceback.print_tb(ex.__traceback__)
		print(traceback.format_exc())
		pass
	finally:
		dt = time.time() - t0
		if bverbose:
			print(f"icompleted = {icompleted}")
			print(f"inumthreads = {inumthreads}")
			print(f"bzip = {bzip}")
			print(f"bfile = {bfile}")
			print(f"bfileclosed = {bfileclosed}")
			print(f"line = {sys._getframe(0).f_lineno}, ifacts = {ifacts}")
			print(f"line = {sys._getframe(0).f_lineno}, len(facts) = {len(facts)}")
			print(f"line = {sys._getframe(0).f_lineno}, ilines = {ilines}")
			print(f"line = {sys._getframe(0).f_lineno}, len(lines) = {len(lines)}")
			print(f"line = {sys._getframe(0).f_lineno}, len(hsh) = {len(hsh)}")
		if bln_keyboard_interrupt or keyboard_interrupt_event.is_set() or icompleted >= inumthreads:
			if len(facts) > 0:
				for f2 in sorted(facts, key=lambda x: x[2]):
					if str(f2[1]) not in hsh:
						hsh[str(f2[1])] = [f2[2],]
					else:
						hsh[str(f2[1])].append(f2[2])
					print(f"{f2[1]}\t\t{f2[2]:,}\t\t{f2[3]}\t\t{len(f2[3])}")
					s = f"{f2[1]}\t{f2[2]:,}\t{f2[3]}\t{len(f2[3])}\n"
					if s not in lines:
						lines.append(s)
			if len(hsh) > 0:
				for k, v in hsh.items():
					print(f"{k}: {v}")
			with lock:
				if bfile and not bfileclosed:
					tfile = time.time()
					if len(lines) > 0:
						try:
							_ = f_txt.writelines(lines)
						except OSError as ose:
							print(traceback.format_exc())
							print(f"file is {directory}\\{filename}")
							print(f"len(lines) is {len(lines)}")
							pass
					_ = f_txt.write("\n") 
					f_txt.flush()
					if not bzip:
						f_txt.close()
					else:
						f_txt.detach()
						f_zip.flush()
						f_zip.close()
					total_file += (time.time() - tfile)
				if bdata and not bdataclosed:
					tdata = time.time()
					if conn.in_transaction:
						curs.execute("COMMIT;")
					conn.commit()
					conn.close()
					total_data += (time.time() - tdata)
			process = psutil.Process(os.getpid())
			memory_mb = round(process.memory_info().rss / 1024 / 1024, 2)
			virtual_mb = round(process.memory_info().vms / 1024 / 1024, 2)
			print("")
			print(f"# {memory_mb:.2f} MB physical memory")
			print(f"# {virtual_mb:.2f} MB virtual memory")
			total = total_factor_combinations + total_factorizations_outer + total_calc_density + total_writer
			if total < dt:
				total = dt
			print(f"# {round(total_factor_combinations/60, 2):.2f} total minutes ({100.0*total_factor_combinations/total:.2f}%) factorCombinations()")
			print(f"# {round(total_factorizations_outer/60, 2):.2f} total minutes ({100.0*total_factorizations_outer/total:.2f}%) factorizations_outer()")
			print(f"# {round(total_calc_density/60, 2):.2f} total minutes ({100.0*total_calc_density/total:.2f}%) calc_density()")
			print(f"# {round(total_writer/60, 2):.2f} total minutes ({100.0*total_writer/total:.2f}%) writer()")
			print(f"# {round(total_file, 2):.2f} total seconds writing to file")
			print(f"# {round(total_data, 2):.2f} total seconds writing to database")
			#print(f"# i0 = {i0}")
			#print(f"# i1 = {i1}")
			#print(f"# i1 - i0 = {i1 - i0}")
			#print(f"# itotal = {itotal} ~ {int(round(itotal/(dt/60), 0)):,} per min")
			print(f"# {round(dt/60, 2):.2f} mins ({round(dt/60/60, 2):.2f} hrs) ~ {int(round((i1 - i0)/(dt/60), 0)):,} per min")
			print("")
			if verbose:
				print(f"# arydivisorsids = {arydivisorsids}")
				print(f"# arythreadids = {arythreadids}")
				print(f"# bln_keyboard_interrupt = {bln_keyboard_interrupt}")
				print(f"# keyboard_interrupt_event.is_set() = {keyboard_interrupt_event.is_set()}")
				print(f"# bln_factors_loop = {bln_factors_loop}")
				print(f"# bln_all_factors_loop = {bln_all_factors_loop}")
				print(f"# bln_writer = {bln_writer}")
				print("")
			if q_in.unfinished_tasks > 0 or q_out.unfinished_tasks > 0 or q_thread_max.unfinished_tasks > 0:
				print(f"# q_in.unfinished_tasks = {q_in.unfinished_tasks}")
				print(f"# q_out.unfinished_tasks = {q_out.unfinished_tasks}")
				print(f"# q_thread_max.unfinished_tasks = {q_thread_max.unfinished_tasks}")
				clear_queue(q_in, "writer() q_in")
				clear_queue(q_out, "writer() q_out")
				clear_queue(q_thread_max, "writer() q_thread_max")
			
			
t0 = 0
total_factorizations_outer = 0.0
total_factor_combinations = 0.0
total_calc_density = 0.0
total_writer = 0.0
total_file = 0.0
total_data = 0.0
istarted = 0
inumthreads = 1
iexit = 0
q_in = queue.Queue()
q_out = queue.Queue()
q_thread_max = queue.Queue()
lock = threading.Lock()

def directory_path(filename):
	global bdata
	global bfile
	
	hsh_dir = {}
	hsh_dir[(1, 'current',   'Current Working Directory ...')] = os.getcwd()
	hsh_dir[(2, 'module',	'Python Module Directory .....')] = pathlib.Path(__file__).parent.resolve()
	hsh_dir[(3, 'home',	  'Home Directory ..............')] = os.path.expanduser('~')
	hsh_dir[(4, 'data',	  'Data Directory ..............')] = platformdirs.user_data_dir()
	hsh_dir[(5, 'documents', 'Documents Directory .........')] = platformdirs.user_documents_dir()
	
	print("Choose a directory to write file to:")
	for key, value in hsh_dir.items():
		print(f"[{key[0]}] {key[2]} {value}")
	print("[6] Custom Path")
	print("[7] Output To Console")
	choice = ""
	try:
		choice = input("Enter your choice (1-7): ")
	except EOFError as eofe:
		pass
	dir_path = ""
	for key in hsh_dir.keys():
		if choice == str(key[0]):
			dir_path = hsh_dir[key]
	
	if dir_path == "":
		if choice == '6':
			dir_path_str = input("Enter the directory path: ")
			dir_path = pathlib.Path(dir_path_str)
		elif choice == '7':
			bdata = False
			bfile = False
		else:
			print("Invalid choice. Please run the script again.")
			sys.exit(1)
	
	if bdata or bfile:
		if not dir_path.exists() or not dir_path.is_dir():
			print(f"Error: The directory '{dir_path}' does not exist.")
			sys.exit(1)
		is_readable = os.access(dir_path, os.R_OK)
		is_writable = os.access(dir_path, os.W_OK)
		permissions = True
		exists = True
		if filename is not None:
			file_path = os.path.join(dir_path, filename)
			exists = os.path.exists(file_path)
			if not exists:
				try:
					with open(file_path, "x") as f:
						f.write("")
				except PermissionError as pe:
					permissions = False
					pass
				exists = os.path.exists(file_path)
		if not is_readable:
			print("Error: You do not have read permissions for this directory.")
		if not is_writable:
			print("Error: You do not have write permissions for this directory.")
		if not permissions:
			print("Error: You do not have permissions for this directory or file.")
		if not exists:
			print("Error: Path to filename does not exist.")
		if not exists or not is_readable or not is_writable or not permissions:
			sys.exit(1)	
		print(f"Selected path '{dir_path}'")
	print("")
	
	return dir_path


keyboard_interrupt_event = threading.Event()
bln_factors_loop = False
bln_all_factors_loop = False
bln_writer = False
bln_keyboard_interrupt = False
bln_sys_exit = False

def dump_all_threads():
    print("\n" + "="*40, file=sys.stderr)
    print(" DUMPING ALL ACTIVE THREADS ", file=sys.stderr)
    print("="*40, file=sys.stderr)
    frames = sys._current_frames()    
    for thread in threading.enumerate():
        print(f"\n--- Thread: {thread.name} (ID: {thread.ident}) ---", file=sys.stderr)
        frame = frames.get(thread.ident)
        if frame:
            traceback.print_stack(frame, file=sys.stderr)
        else:
            print("  <No stack trace available>", file=sys.stderr)            
    print("\n" + "="*40, file=sys.stderr)

def clear_queue(q, msg):
	global verbose
	
	with q.mutex:
		if verbose: 
			print(f"clear_queue() {msg} q.unfinished_tasks = {q.unfinished_tasks}")
			#print(f"clear_queue() {msg} q.qsize() = {q.qsize()}")
			#print(f"clear_queue() {msg} q.empty() = {q.empty()}")
		if q.unfinished_tasks > 0:
			q.queue.clear()
			q.unfinished_tasks = 0
			q.all_tasks_done.notify_all()

def graceful_exit(signum, frame):
	global keyboard_interrupt_event
	global bln_keyboard_interrupt
	global bln_factors_loop
	global bln_all_factors_loop
	global bln_writer
	global bln_sys_exit
	global q_in
	global q_out
	global q_thread_max
	global verbose
	global th
	global writer_th
	global inumthreads
	global istarted
	global icompleted
	global iexit
	if verbose: print(f"graceful_exit(signum = {signum}, frame = {frame})")
	
	iexit += 1
	if iexit >= 3:
		verbose = True
	if keyboard_interrupt_event.is_set():
		icompleted = inumthreads
	
	keyboard_interrupt_event.set()
	bln_keyboard_interrupt = True
	bln_factors_loop = False
	bln_all_factors_loop = False
	bln_writer = False
	
	clear_queue(q_in, "q_in")
	clear_queue(q_out, "q_out")
	clear_queue(q_thread_max, "q_thread_max")
	if writer_th and writer_th.is_alive():
		q_out.put(None)
	if verbose:
		print(f"inumthreads = {inumthreads}")
		print(f"istarted = {istarted}")
		print(f"icompleted = {icompleted}")
		for t in range(0, inumthreads):
			print(f"thread[{t}].is_alive() ? {th[t].is_alive()}")
		print(f"writer_thread.is_alive() ? {writer_th.is_alive()}")
		dump_all_threads()
		
	if bln_sys_exit:
		sys.exit(0)


if hasattr(signal, 'SIGTERM'):
	signal.signal(signal.SIGTERM, graceful_exit)
if hasattr(signal, 'SIGINT'):
	signal.signal(signal.SIGINT, graceful_exit)
if hasattr(signal, 'SIGBREAK'):
	signal.signal(signal.SIGBREAK, graceful_exit)
if hasattr(signal, 'SIGSTOP'):
	signal.signal(signal.SIGSTOP, graceful_exit)
if hasattr(signal, 'SIGTSTP'):
	signal.signal(signal.SIGTSTP, graceful_exit)


th = []
writer_th = None

"""
import math
import matplotlib.pyplot as plt
ary = [int(line.split()[1].replace(",", "")) for line in open("D:\\Python\\Sequence\\sequence (1,2).txt") if len(line.split()) > 1]
plt.plot(ary, marker='o', linestyle='-', color='b')
plt.grid(True)
plt.show()
plt.plot([math.log(a) for a in ary], marker='o', linestyle='-', color='b')
plt.grid(True)
plt.show()
"""

# 
# main loop 
# 
# i7-1165G7 @ 2.80GHz, Python 3.14.2					           #	  65,536 #   1.52 mins ( 0.03 hrs)  42,913 per min
# i7-1165G7 @ 2.80GHz, Python 3.13.11					           #   1,145,760 #  14.22 mins ( 0.24 hrs)  67,117 per min
# i7-1165G7 @ 2.80GHz, Python 3.13.11					           #   1,048,576 #  12.40 mins ( 0.21 hrs)  76,968 per min
# i7-1165G7 @ 2.80GHz, Python 3.13.11					           #   8,388,608 # 335.85 mins ( 5.60 hrs)  24,102 per min
# i7-1165G7 @ 2.80GHz, Python 3.14.2					           #   8,388,608 # 189.24 mins ( 3.15 hrs)  44,278 per min
#														               8,388,608 # 139.40 mins ( 2.30 hrs)
# 
# i7-1165G7 @ 2.80GHz, Python 3.14.4, threads = 1, bln_numba = False                    #   1,048,576 #   9.62 mins ( 0.16 hrs)  99,232 per min
# i7-1165G7 @ 2.80GHz, Python 3.14.4, threads = 1, bln_numba = True                     #   1,048,576 #   7.13 mins ( 0.12 hrs) 133,922 per min
# i7-1165G7 @ 2.80GHz, Python 3.14.6, threads = 2, bln_cpp = True, thread_local = True  #   1,048,576 #   1.80-1.95 mins ( 0.03 hrs) 488,231-529,661 per min
# i7-1165G7 @ 2.80GHz, Python 3.14.6, threads = 4, bln_cpp = True, thread_local = True  #   1,048,576 #   1.31-1.33 mins ( 0.02 hrs) 715,623-726,878 per min
# i7-1165G7 @ 2.80GHz, Python 3.14.6, threads = 1, bln_cpp = True, thread_local = True  #   4,194,304 #  12.55 mins (0.21 hrs) 309,639 per min
# i7-1165G7 @ 2.80GHz, Python 3.14.6, threads = 2, bln_cpp = True, thread_local = True  #   4,194,304 #   
# i7-1165G7 @ 2.80GHz, Python 3.14.6, threads = 4, bln_cpp = True, thread_local = True  #   4,194,304 #   7.70-8.56 mins (0.14 hrs) 454,186-504,910 per min
# i7-1165G7 @ 2.80GHz, Python 3.14.6, threads = 4, bln_cpp = True, thread_local = False #   4,194,304 #   9.34 mins (0.14 hrs) 416,163 per min
# 
#  i7-1360P @ 2.20GHz, Python 3.14.6, threads = 2, bln_cpp = True, thread_local = True  #   4,194,304 #   6.27 mins (0.10 hrs) 620,227 per min
#  i7-1360P @ 2.20GHz, Python 3.14.6, threads = 2, bln_cpp = True, thread_local = False #   4,194,304 #   7.46 mins (0.12 hrs) 520,896 per min
# 
#  i7-1360P @ 2.20GHz, Python 3.14.2, threads = 1, bln_numba = True  #   8,388,608 #  36.42 mins ( 0.61 hrs) 222,272 per min
#  i7-1360P @ 2.20GHz, Python 3.14.2, threads = 1, bln_numba = True  # 134,217,728 # 947.44 mins (15.79 hrs) 140,827 per min
#  i7-1360P @ 2.20GHz, Python 3.14.2, threads = 1, bln_cpp = True    #   1,048,576 #   1.94 mins ( 0.03 hrs) 491,668 per min
#  i7-1360P @ 2.20GHz, Python 3.14.2, threads = 1, bln_cpp = True    #   1,048,576 #   0.97 mins ( 0.02 hrs) 981,526 per min
#  i7-1360P @ 2.20GHz, Python 3.14.2, threads = 1, bln_cpp = True    #   8,388,608 #  17.53 mins ( 0.29 hrs) 461,648 per min
#  i7-1360P @ 2.20GHz, Python 3.14.2, threads = 1, bln_cpp = True    #   8,388,608 #  13.13 mins ( 0.22 hrs) 616,387 per min
#  i7-1360P @ 2.20GHz, Python 3.14.2, threads = 1, bln_cpp = True    # 134,217,728 # 362.13 mins ( 6.04 hrs) 368,451 per min
# 
# python3.14t.exe -m pip install git+https://github.com/AlexWeslowski/Divisors.git
# python3.14t.exe -m pip install --upgrade --pre numpy
# python3.14t.exe -X faulthandler "D:\Python\Sequence\sequence_th.py" 2 [(1,2)] 2 1048576
# python3.14t.exe -m memory_profiler "H:\Python\Sequence\sequence_th.py" 2 [(1,2)] 2 8388608
# python3.14t.exe "D:\Python\Sequence\sequence_th.py" 4 [(1,2)] 2 4194304 --thread_local
# python3.14t.exe "H:\Python\Sequence\sequence_th.py" 2 [(1,4)] 2 1073741824
# python3.14t.exe "H:\Python\Sequence\sequence_th.py" 2 [(1,2),(1,3),(1,4),(1,5)] 2 1073741824
# 
# @memory_profiler.profile
def main():
	global verbose
	global directory
	global filename
	global setfractions
	global q_in
	global q_out
	global th
	global writer_th
	global t0
	global bln_cpp
	global bln_numba
	global save_memory
	global aryprimes
	global inumthreads
	global istarted
	global icompleted
	global keyboard_interrupt_event
	global bln_keyboard_interrupt
	global bln_factors_loop
	global bln_all_factors_loop
	global bln_writer
	global bln_sys_exit
	global factscache
	global linescache
		
	print(f"Python {sys.version}")
	cpu_info = cpuinfo.get_cpu_info()
	brand_raw = cpu_info.get('brand_raw', 'Unknown Processor')
	hz_advertised = cpu_info.get('hz_advertised_friendly', '')
	hz_actual = cpu_info.get('hz_actual_friendly', '')
	if brand_raw.find("GHz") == -1:
		hz_ary = hz_actual.split(" ")
		if len(hz_ary) > 1:
			try:
				hz = round(float(hz_ary[0]), 2)
				hz_actual = hz_actual.replace(hz_ary[0], f"{hz:.2f}")
			except ValueError as ve:
				pass
		if hz_actual != "":
			hz_actual = hz_actual.replace(" ", "")
			brand_raw = f"{brand_raw} @ {hz_actual}"
	print(brand_raw)
	print("")
	args = sys.argv[1:]

	if "--v" in args or "--verbose" in args:
		verbose = True
	
	if "--numba" in args:
		bln_cpp = False
		bln_numba = True
	
	if bln_cpp and ("--memory" in args or "--savememory" in args or "--save_memory" in args):
		save_memory = True
	
	if len(args) > 0 and args[0].lower() == "debug":
		# import sqlite3
		conn = sqlite3.connect(f"{directory}\\sequence.bin", check_same_thread=False)
		curs = conn.cursor()
		_ = curs.execute("SELECT DISTINCT ord FROM sequence WHERE ord > (SELECT max(ord)-32 FROM sequence) LIMIT 32")
		print(curs.fetchall())
		return 
	elif len(args) < 4:
		print("Must pass 4 arguments sequence_th.py inumthreads aryfractions istart ifinish")
		print("For example sequence_th.py 1 [(1,2)] 2 1048576")
		return
	
	thread_local = False
	if ("--threadlocal" in args or "--thread_local" in args):
		thread_local = True
	
	imult = 8192
	istarted = 0
	inumthreads = int(args[0])
	if inumthreads == 1:
		factscache = 2
		linescache = 4
	ary = eval(args[1])
	strary = str(ary)[1:-1].replace("),(", ") (").replace(", ", ",")
	setfractions = frozenset([divisors.BoostRational(tpl[0], tpl[1]) if bln_cpp else Fraction(tpl[0], tpl[1]) if bln_numba else fractions.Fraction(tpl[0], tpl[1]) for tpl in ary])
	istepby = 1
	if len(setfractions) == 1:
		istepby = list(setfractions)[0].denominator
	filename = f"sequence {strary}.txt"
	directory = directory_path(filename)
	
	i0, i1 = int(args[2]) - inumthreads * imult, int(args[3])
	#if i1 > div.size():
	#	isize = div.resize(i1)
	#	if i1 > isize:
	#		print(f"main() this code not valid for ifinish > {isize:,} ifinish={i1:,} (2**{round(math.log(i1, 2), 2):.2f})")
	#		return
	if i0 > i1:
		print(f"main() istart > ifinish (istart={i0:,} ifinish={i1:,})")
		return
	if i0 < 2:
		i0 = 2
	
	print(f"main() starting process with inumthreads = {inumthreads}, setfractions={ary}, istart={i0}, ifinish={i1}")
	print(f"main() verbose={verbose}, numba={bln_numba}, cpp={bln_cpp}, threadlocal={thread_local}")
	print(f"main() {datetime.datetime.now().strftime('%I:%M:%S %p')}")

	# inumthreads, i0, i1 = 2, 2, 32768
	# i, imult = i0, 8192
	# while i < i1:
	#   for t in range(0, inumthreads):
	#	   print((i + t * imult, min(i1, i + (t + 1) * imult)))
	#   i += inumthreads * imult
	i, t0 = i0, time.time()
	
	if True:
		bln_factors_daemon = True
		bln_writer_daemon = False
		
		if i > 12:
			fill_hsh(i)
		
		for frac in setfractions:
			if i0 <= frac.denominator:
				q_out.put([(frac.denominator, Fraction(1, frac.denominator), frac.denominator, [frac.denominator,]),])
		
		th = [object(),] * inumthreads
		while i < i1:
			for t in range(0, inumthreads):
				a = i + t * imult
				b = i + (t + 1) * imult
				if istepby > 1:
					while a % istepby > 0:
						a += 1
					while b % istepby > 0:
						b += 1
				if b >= i1:
					b = i1 + istepby
				if verbose: 
					print(f"q_in.put(({a}, {b}))")
				q_in.put((a, b))
			i += inumthreads * imult
		_ = threading.stack_size(33554432)
		for t in range(0, inumthreads):
			# th[t] = threading.Thread(target=all_factors_loop, args=(i1, t, thread_local, q_in, q_out, q_thread_max, istepby), daemon=bln_factors_daemon)
			# factors_loop(t0, i0, i1, i2, bbreak)
			th[t] = threading.Thread(target=factors_loop, args=(i1, t, thread_local, q_in, q_out, q_thread_max, istepby, False), daemon=bln_factors_daemon)
			th[t].start()
		for t in range(0, inumthreads):
			q_in.put(None)
		print(f"main() istarted = {istarted}, inumthreads = {inumthreads}")
		while istarted < inumthreads and not keyboard_interrupt_event.is_set():
			time.sleep(1)
			print(f"main() istarted = {istarted}, inumthreads = {inumthreads}")
		print("")
		
		writer_th = threading.Thread(target=writer, args=(q_out, q_thread_max), daemon=bln_writer_daemon)
		writer_th.start()
		try:
			while icompleted < inumthreads and not keyboard_interrupt_event.is_set():
				time.sleep(2)
		except KeyboardInterrupt:
			graceful_exit()
		try:
			for t in range(0, inumthreads):
				while th[t].is_alive() and not keyboard_interrupt_event.is_set():
					th[t].join()
			writer_th.join()
		except KeyboardInterrupt:
			graceful_exit()
	
		

if __name__ == '__main__':
	main()
