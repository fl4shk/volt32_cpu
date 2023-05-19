#!/usr/bin/env python3

import sys
import math
import enum
from enum import auto

#--------
class Blank:
	pass

def psconcat(*args):
	return str().join([str(arg) for arg in args])

def lsconcat(lst):
	#return str().join([str(elem) for elem in lst])
	return psconcat(*lst)

def fprintout(file, *args, flush=False):
	print(psconcat(*args), sep="", end="", file=file, flush=flush)

def printout(*args):
	fprintout(sys.stdout, *args)

def printerr(*args):
	fprintout(sys.stderr, *args)

def convert_enum_to_str(to_conv):
	return str(to_conv)[str(to_conv).find(".") + 1:]

def convert_str_to_enum_opt(to_conv, EnumT, STR_ENUM_MAP):
	if not (isinstance(to_conv, EnumT) or isinstance(to_conv, str)):
		raise TypeError(psconcat("convert_str_to_enum_opt() error: ",
			to_conv, " ", type(to_conv)))

	if isinstance(to_conv, EnumT):
		return to_conv
	else: # if isinstance(to_conv, str):
		if to_conv not in STR_ENUM_MAP:
			raise KeyError(to_conv)
		return STR_DIRECTION_MAP[to_conv]

def obj_err_str(obj, i=None, lst=None):
	if i is None:
		return psconcat("{!r}, {}".format(obj, type(obj)))
	else: # if i is not None:
		assert isinstance(i, int), \
			obj_err_str(i)
		assert lst is None or isinstance(lst, list), \
			obj_err_str(lst)

		if lst is None:
			return psconcat("{}, {!r}, {}".format(i, obj, type(obj)))
		else: # if isinstance(lst, list):
			return psconcat("{!r}, {}".format(lst, obj_err_str
				(obj, i, None)))
#--------
class TypeSz(enum.Enum):
	Sz8 = 8
	Sz16 = 16
	Sz32 = 32
	Sz64 = 64

# Data LAR Metadata needed to figure how vector type casting should work
class Metadata:
	def __init__(self, typesz: TypeSz=TypeSz.Sz8, soffs: int=0):
		self.set_typesz(typesz)
		self.set_soffs(soffs)

	def set_typesz(self, n_typesz: TypeSz):
		self._typesz = n_typesz
	def typesz(self) -> TypeSz:
		return self._typesz

	def set_soffs(self, n_soffs: int):
		self._soffs = n_soffs
	def soffs(self) -> int:
		return self._soffs
	def soffs_nbits(self) -> int:
		return int(math.log2(self.nelems()))
	def nelems(self) -> int:
		return self.nbytes() // (self.typesz().value // 8)

	def aligned_soffs_inv_mask(self):
		max_nbits = self.max_nbits()
		soffs_nbits = self.soffs_nbits()
		return ((1 << (max_nbits - soffs_nbits)) - 1)
	def aligned_soffs(self) -> int:
		return self.soffs() & ~self.aligned_soffs_inv_mask()
	def other_typesz_aligned_soffs(self, other_typesz: TypeSz) -> int:
		#return (self.soffs()
		#	& (int(math.log2(other.nelems())) + 1)
		temp_md = Metadata(typesz=other_typesz, soffs=self.soffs())
		return temp_md.aligned_soffs()

	@staticmethod
	def casted_vec_info(md_to, md_from):
		max_nbits = Metadata.max_nbits()
		ret = dict()
		ret["vsz"] = (
			(
				1
				<< (
					max_nbits
					- abs(md_from.soffs_nbits() - md_to.soffs_nbits())
				)
			)
		)

		if md_to.typesz().value == md_from.typesz().value:
			# no casting needed
			return None
		elif md_to.typesz().value > md_from.typesz().value:
			# up-casting
			ret["vsel"] = "from"
			ret["vtype"] = md_from.typesz().name
			#ret["vind"] = (
			#	#md_from.soffs() & md_to.aligned_soffs_inv_mask()
			#	md_from.other_typesz_aligned_soffs(md_to.typesz())
			#)
			#ret["voffs"] = (
			#	ret["vind"] * md_to.nelems()
			#)
			ret["voffs"] = (
				#md_to.soffs() & md_from.aligned_soffs_inv_mask()
				md_from.other_typesz_aligned_soffs(md_to.typesz())
			)
			ret["vind"] = (
				ret["voffs"] // md_to.nelems()
			)
		else: # if md_to.typesz().value < md_from.typesz().value:
			# down-casting
			ret["vsel"] = "to"
			ret["vtype"] = md_to.typesz().name
			#ret["vind"] = (
			#	#md_to.soffs() & md_from.aligned_soffs_inv_mask()
			#	md_to.other_typesz_aligned_soffs(md_from.typesz())
			#)
			#ret["voffs"] = (
			#	ret["vind"] * md_from.nelems()
			#)
			ret["voffs"] = (
				md_to.other_typesz_aligned_soffs(md_from.typesz())
			)
			ret["vind"] = (
				ret["voffs"] // md_from.nelems()
			)
		return ret

	@staticmethod
	def nbytes() -> int:
		#return 128
		#return 32
		return (TypeSz.Sz32.value // 8)
	@staticmethod
	def max_nbits() -> int:
		return int(math.log2(Metadata.nbytes()))

	def __repr__(self):
		typesz_name = self.typesz().name
		soffs = self.soffs()
		srsoffs = soffs >> ((self.typesz().value // 8) - 1)
		nelems = self.nelems()
		#return "({}, {})".format(self.typesz().name, self.soffs())
		return (
			#"(sz:{typesz_name} soffs:{soffs} srsoffs:{srsoffs})"
			f"({typesz_name} {soffs} {srsoffs} {nelems})"
			#.format(
			#	typesz_name=typesz_name,
			#	soffs=hex(soffs),
			#	srsoffs=hex(srsoffs),
			#)
		)

#def align_soffs(md_to: Metadata, md_from: Metadata) -> int:
#	if md_to.typesz().value == md_from.typesz().value:
#		# no casting needed
#		return md_to.aligned_soffs()
#	elif md_to.typesz().value > md_from.typesz().value:
#		# up-casting
#		#return md_from.downcasted_soffs(md_to.typesz())
#		return md_from.aligned_soffs(md_to.typesz())
#	else: # if md_to.typesz().value < md_from.typesz().value:
#		# down-casting
#		#return md_to.upcasted_soffs(md_from.typesz())
#		return md_to.aligned_soffs(md_from.typesz())

typesz_lst = [
	TypeSz.Sz8, TypeSz.Sz16, TypeSz.Sz32,
	#TypeSz.Sz64,
]
#md_lst = [Metadata(typesz=typesz, soffs=soffs)
#	for typesz_lst, range(Metadata.nbytes())]
md_lst = []
for typesz in typesz_lst:
	#md_lst.append([])
	for soffs in range(Metadata.nbytes() // (typesz.value // 8)):
		to_append = Metadata(
			typesz=typesz,
			#soffs=soffs << ((typesz.value // 8) - 1)
			soffs=soffs * (typesz.value // 8)
		)
		#print(to_append)
		#md_lst[-1] += [to_append]
		md_lst += [to_append]

with open("output.txt.ignore", "w") as f:
	#def run_test(md_to: Metadata, md_from: Metadata):
	#	casted = cast_soffs(md_to=md_to, md_from=md_from)
	#	print(r"to:{md_to} from:{md_from} {casted}")
	for md_to in md_lst:
		for md_from in md_lst:
			if md_to.typesz().value != md_from.typesz().value:
				#casted = cast_soffs(md_to=md_to, md_from=md_from)
				#aligned = align
				casted_vec_info = Metadata.casted_vec_info(
					md_to=md_to, md_from=md_from
				)
				print(
					(
						"nbytes:{} "
						+ "to:{} from:{} "
						+ "vinfo:("
							+ "{} {} {} o:{} i:{}"
						+ ")"
						#+ "vinfo:({} {} {} {})"
						#+ "vinfo:({} {} {})"
						#+ "vinfo:(vtype:{} vsz:{} voffs:{})"
					)
					.format(
						Metadata.nbytes(),
						md_to, md_from,
						casted_vec_info["vsel"],
						casted_vec_info["vtype"],
						casted_vec_info["vsz"],
						casted_vec_info["voffs"],
						casted_vec_info["vind"],
					),
					file=f
				)
#--------
