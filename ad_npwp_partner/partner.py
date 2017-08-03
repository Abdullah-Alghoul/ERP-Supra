from osv import osv, fields
from tools.translate import _
import time
from ad_account_optimization.report.common_report_header import common_report_header
from report import report_sxw

class partner(osv.osv):
	_inherit = ["res.partner","mail.thread"]
	_name = "res.partner"
	_columns = {
			'create_uid': fields.many2one('res.users', 'Creator', required=True, readonly=True),
			'npwp' : fields.char('No. NPWP', size=20, required=False, help='Misal 01.540.674.7.431-000',track_visibility='onchange'),
			'name' : fields.char('Name',track_visibility='onchange'),
			'blok':fields.char('Blok',track_visibility='onchange'),
			'nomor':fields.char('Nomor',track_visibility='onchange'),
			'rt':fields.char('RT',size=3,track_visibility='onchange'),
			'rw':fields.char('RW',size=3,track_visibility='onchange'),
			'kelurahan':fields.char('Kelurahan',track_visibility='onchange'),
			'kecamatan':fields.char('Kecamatan',track_visibility='onchange'),
			'kabupaten':fields.char('Kabupaten',track_visibility='onchange'),
			'propinsi':fields.char('Propinsi',track_visibility='onchange'),
			'street':fields.char('street',track_visibility='onchange'),
			'street2':fields.char('street',track_visibility='onchange'),
		}

	def onchange_format_npwp(self, cr, uid, ids, npwp):
		if npwp:
			if npwp=='11111111111111111111':
				return {'value': {'npwp': '11111111111111111111'}}
			else:
				result = ''
				warning = {"title": ("NPWP Number Format Incorrect!"), "message": ("Masukan 15 digit NPWP tanpa tanda baca")}
				if len(npwp) != 15 :
					return {'warning': warning, 'value': {'npwp': result}}
				elif not npwp.isdigit():
					return {'warning': warning, 'value': {'npwp': result}}
				else:
					result = npwp[:2] + '.' + npwp[2:5] + '.' + npwp[5:8] + '.' + npwp[8] + '-' + npwp[9:12] + '.' + npwp[-3:] 
					return {'value': {'npwp': result}}
		return True

	def create(self, cr, uid, vals, context=None):
		if 'parent_id' in vals:
			return super(partner, self).create(cr, uid, vals, context=context)
		else:
			if vals['is_company']==True:
				if 'npwp' in vals:
					if vals['npwp']=='11111111111111111111':
						vals['npwp']=='11111111111111111111'
				else:
					cek=self.pool.get('res.partner').search(cr,uid,[('npwp', '=' ,vals['npwp'])])
					if cek:
						raise osv.except_osv(('Perhatian..!!'), ('No NPWP Unique ..'))
		return super(partner, self).create(cr, uid, vals, context=context)

	def write(self,cr,uid,ids,vals,context={}):
		cek=self.pool.get('res.partner').search(cr,uid,[('id', '=' ,ids)])
		user_id=self.pool.get('res.users').search(cr,uid,[('id', '=' ,uid)])
		# Harus Administrator
		# if 'name' in vals:
			# if uid <> 1: # Yang merubah harus Administrator
				# raise osv.except_osv(('Warning..!!'), ('Please Contact Administrator To Change Customer Name ..'))	

		user_a =self.pool.get('res.partner').browse(cr,uid,user_id)
		# user_name=self.pool.get('res.users').browse(cr,uid,[('id', '=' ,user_id)])

		for hasil in self.pool.get('res.partner').browse(cr,uid,cek):
			if 'npwp' in vals:
				#  Jika dia Supplier Invoice
				n  = self.pool.get('ir.model.data')
				# id_group_supplier = n.get_object(cr, uid, 'sbm_inherit', 'group_customer_invoice_admin_creator').id
				user_group_supplier = self.pool.get('res.groups').browse(cr, uid, 85)

				b = False
				for x in user_group_supplier.users:
					if x.id == uid:
						b = True

				#  Jika dia Admin Invoice
				m  = self.pool.get('ir.model.data')
				id_group = m.get_object(cr, uid, 'sbm_inherit', 'group_customer_invoice_admin_creator').id
				user_group = self.pool.get('res.groups').browse(cr, uid, id_group)

				a = False
				for x in user_group.users:
					if x.id == uid:
						a = True

				print '=============Cek Admin Invoice====',a
				print '=============Cek Supplier Invoice====',b

				if uid <> 1:
					if uid <> hasil.create_uid.id: # Jika bukan yang buat
						if a == False and b == False: # Jika bukan admin invoice
							raise osv.except_osv(('Warning..!!'), ('Please Contact Creator Customer '+ hasil.name +' To Change Customer NPWP..'))

			if hasil['is_company']==True:
				# NPWP di awal tidak ada, maka hasilnya False
				if 'npwp' in hasil:
					if hasil['npwp']==False:
						if vals['npwp']=='11111111111111111111':
							vals['npwp']=='11111111111111111111'
						else:
							cek=self.pool.get('res.partner').search(cr,uid,[('npwp', '=' ,vals['npwp']),('is_company','=',True)])
							if cek:
								raise osv.except_osv(('Perhatian..!!'), ('No NPWP Unique ..'))
				
				# NPWP awal ada valuenya
				else:
					if 'npwp' in vals:
						if vals['npwp']=='11111111111111111111':
							vals['npwp']=='11111111111111111111'
						else:
							cek=self.pool.get('res.partner').search(cr,uid,[('npwp', '=' ,vals['npwp']),('is_company','=',True)])
							if cek:
								raise osv.except_osv(('Perhatian..!!'), ('No NPWP Unique ..'))
							
		return super(partner, self).write(cr, uid, ids, vals, context=context)

partner()


class AccountInvoice(osv.osv):
	_inherit = "account.invoice"
	_columns = {
			'kmk': fields.char('KMK', size=64, select=True),
			'kurs': fields.float('Kurs BI', digits=(12,2), select=True),
			'pajak': fields.float('Kurs Pajak', digits=(12,2), select=True),
			'kwitansi': fields.char('Kwitansi', size=64, select=True),
			'faktur_pajak_no' : fields.char('Faktur Pajak', size=20, required=False, help='Misal 010.000-10.00000001'),
	}
	
	def onchange_format_faktur(self, cr, uid, ids, no):
		try:
			int(no)
			if len(no) == 16:
				value = list(no)
				value.insert(3, '.')
				value.insert(7, '-')
				value.insert(10, '.')
				result = "".join(value)
				return {'value': {'faktur_pajak_no': result}}      
			else:
				return {'warning': {"title": _("Perhatian"), "message": _("Nomor faktur pajak harus 16 digit")}, 'value': {'faktur_pajak_no': False}}
		except:
			return {'warning': {"title": _("Perhatian"), "message": _("Masukan 16 digit angka tanpa separator")}, 'value': {'faktur_pajak_no': False}}
		
		
AccountInvoice()

