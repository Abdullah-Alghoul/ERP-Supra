from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from stock import stock
from openerp import pooler
import math
import time
from datetime import datetime, timedelta
import webbrowser
import netsvc
import openerp.exceptions
from osv import osv, fields
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp


from openerp import netsvc
class stock_picking(osv.osv):
	def open_full_record(self, cr, uid, ids, context=None):
		data= self.browse(cr, uid, ids, context=context)
		
		return {
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'action_id':588,
			'view_id':960,
			'res_model': self._name,
			'res_id': data[0].backorder_id.id,
			'target': 'current',
			'context': context,  # May want to modify depending on the source/destination
		}
	_inherit = 'stock.picking'
	_columns = {
		'cust_doc_ref' : fields.char('External Doc Ref',200,required=False,store=True),
		'lbm_no' : fields.char('LBM No',200,required=False,store=True),
	}


	
stock_picking()

class stock_picking_in(osv.osv):
	_inherit = 'stock.picking.in'
	_table="stock_picking"
	_columns = {
		'cust_doc_ref' : fields.char('External Doc Ref',200,required=False,store=True),
		'lbm_no' : fields.char('LBM No',200,required=False,store=True),
	}

	def action_process(self, cr, uid, ids, context=None):
		# picking_obj = self.browse(cr, uid, ids, context=context)
		picking_obj=self.pool.get('stock.picking.in').browse(cr, uid, ids)

		if(picking_obj[0].cust_doc_ref is None or picking_obj[0].cust_doc_ref is False):
			raise osv.except_osv(('Warning !!!'), ('Plase Fill "External Doc Ref" Field!!'))
		else:
			if picking_obj[0].backorder_id.cust_doc_ref == picking_obj[0].cust_doc_ref:
				raise osv.except_osv(('Warning !!!'), ('External Doc Ref can\'t same with backorder External Doc Ref, Please Change External Doc Reference Field !'))
			else:
				return super(stock_picking_in, self).action_process(cr, uid, ids, context)

				
	
stock_picking_in()


# INHERIT FOR
# 1. TOTAL DISCOUNT
# 2. DESCRIPTION LINE MANY2ONE RELATED
class PurchaseOrder(osv.osv):
	_inherit='purchase.order'
	# _columns={
	# 	'bank_statement_lines':fields.one2many('account.bank.statement.line','po_id',string="First Payments"),
	# }

	def actionInvoiceRefund(self,cr,uid,ids,context=None):
		searchConf = self.pool.get('ir.config_parameter').search(cr, uid, [('key', '=', 'base.print')], context=context)
		browseConf = self.pool.get('ir.config_parameter').browse(cr,uid,searchConf,context=context)[0]
		urlTo = str(browseConf.value)+"report-accounting/nota-retur&id="+str(ids[0])+"&uid="+str(uid)
		# urlTo = 'http://localhost/OpenPrint/web/index.php?r='+"report-accounting/nota-retur&id="+str(ids[0])+"&uid="+str(uid)
		return {
			'type'	: 'ir.actions.client',
			'target': 'new',
			'tag'	: 'print.out',
			'params': {
				# 'id'	: ids[0],
				'redir'	: urlTo
			},
		}
	def _get_total_discount(self, cr, uid, ids, name, arg, context=None):
		dis = {}
		discount=0
		totaldiscount=0
		
		orders= self.browse(cr, uid, ids, context=context)
		for order in orders:
			discount = order.amount_bruto-order.amount_untaxed
			# if rupiah and discount < 999
			if discount < 999 and order.pricelist_id.id==2:
				discount = 0.00
			dis[order.id]=discount
			
		return dis


	def _get_amount_bruto(self,cr,uid,ids,name,arg,context=None):
		orders= self.browse(cr, uid, ids, context=context)
		total = {}
		for order in orders:
			total[order.id] = 0
			for line in order.order_line:
				if line.product_qty==1 and order.pricelist_id.id==2:
					subtotal = line.price_subtotal
				else:
					subtotal = line.product_qty*line.price_unit
				total[order.id] = total[order.id]+subtotal

		return total

	def _default_total_discount(self,cr,uid,context=None):
		res = 0
		return res

	_columns = {
		'total_discount': fields.function(
			_get_total_discount,string="Total Discount",type="float",store=False
		),
		'amount_bruto':fields.function(
			_get_amount_bruto,
			string="SubTotal",
			type="float",
			store=False
		),
		'description': fields.related('order_line','name', type='text', string='Description',store=False),
	}
	_defaults = {
		'total_discount': _default_total_discount
	}



	def invoice_dp_bank_statment(self, cr, uid, ids, context=None):
		mod_obj = self.pool.get('ir.model.data')
		act_obj = self.pool.get('ir.actions.act_window')
		act_acc_line = self.pool.get('account.bank.statement.line')

		result = mod_obj.get_object_reference(cr, uid, 'account', 'action_bank_statement_tree')
		id = result and result[1] or False
		result = act_obj.read(cr, uid, [id], context=context)[0]
		inv_ids = []
		
		po_id=act_acc_line.search(cr,uid,[('po_id', '=' ,ids)])
		data_po=act_acc_line.browse(cr,uid,po_id)
		for po in data_po:
			inv_ids+= [po.statement_id.id]
		if not inv_ids:
			raise osv.except_osv(_('Error!'), _('No Invoice DP.'))
		if len(inv_ids)>1:
			result['domain'] = "[('id','in',["+','.join(map(str, inv_ids))+"])]"
		else:
			res = mod_obj.get_object_reference(cr, uid, 'account', 'view_bank_statement_form')
			result['views'] = [(res and res[1] or False, 'form')]
			result['res_id'] = inv_ids and inv_ids[0] or False
		return result

		
PurchaseOrder()

class PurchaseOrderLine(osv.osv):
	_inherit='purchase.order.line'
	# _name='purchase.order.line'

class SpecialWorkOrder(osv.osv):
	_inherit = 'perintah.kerja'
	name = 'special.work.order'
	_columns = {
		'special': fields.boolean('Special WO'),
		'pr_id':fields.many2one('pr',string='PR',required=False, domain=[('state','=','confirm')]),
	}
	
	def pr_change(self, cr, uid, ids, pr):
		if pr:
			res = {}; line = []
			obj_spr = self.pool.get('pr').browse(cr, uid, pr)
			res['kontrak'] = obj_spr.ref_pr
			res['partner_id'] = obj_spr.customer_id.id
			res['kontrakdate'] = obj_spr.tanggal
			res['workshop'] = obj_spr.location
			return  {'value': res}
		return True


SpecialWorkOrder()


class SpecialDN(osv.osv):
	_inherit = 'delivery.note'
	_columns = {
		'special': fields.boolean('Special WO'),
		# 'work_order_id': fields.many2one('perintah.kerja',string="SPK",store=True,required=False,domain=[('special','=',True)])
		'work_order_id': fields.many2one('perintah.kerja',string="SPK",store=True,required=False),
		# 'pb_id' : fields.many2one('purchase.requisition.subcont','No PB',readonly=True),
		'work_order_in': fields.many2one('perintah.kerja.internal',string="SPK Internal")
	}

	def spk_change(self, cr, uid, ids, spk):
		if spk:
			res = {}; line = []
			obj_spk = self.pool.get('perintah.kerja').browse(cr, uid, spk)
			res['poc'] = obj_spk.kontrak
			res['partner_id'] = obj_spk.partner_id.id
			res['partner_shipping_id'] = obj_spk.partner_id.id
			return  {'value': res}
		return True

	def spk_change_internal(self, cr, uid, ids, spk):
		if spk:
			res = {}; line = []
			obj_spk = self.pool.get('perintah.kerja.internal').browse(cr, uid, spk)
			res['poc'] = obj_spk.kontrak
			res['partner_id'] = obj_spk.partner_id.id
			res['partner_shipping_id'] = obj_spk.partner_id.id
			return  {'value': res}
		return True


SpecialDN()

# class tesAccountInvoice(osv.osv):
# 	_inherit = 'account.invoice'
	
# 	def _getR():
# 		return "a"
	
# 	_columns={
# 		'tes':fields.function(_getR,string="Tes",store=False,required=False)
# 	}






class PurchaseOrderFullInvoice(osv.osv):
	_inherit='purchase.order'
	# def action_invoice_create(self, cr, uid, ids, context=None):
	
	# 	return False

	# def action_invoice_create(self, cr, uid, ids, context=None):
	# 	return super(purchase_order, self).action_invoice_create(cr, uid, ids, context)

	# BUTTON FULL INVOICE APPEND disc_amount data
	def _prepare_inv_line(self, cr, uid, account_id, order_line, context=None):
		return {
			'name': order_line.name,
			'account_id': account_id,
			'price_unit': order_line.price_unit or 0.0,
			'quantity': order_line.product_qty,
			'product_id': order_line.product_id.id or False,
			'uos_id': order_line.product_uom.id or False,
			'invoice_line_tax_id': [(6, 0, [x.id for x in order_line.taxes_id])],
			'account_analytic_id': order_line.account_analytic_id.id or False,
			# 'amount_discount':order_line.discount_nominal
		}
	def _prepare_inv_line_for_discount(self, cr, uid, account_id,discountNominal, invoiceLineTaxId, product_discount, context=None):			
		return {
			'product_id': product_discount,
			'name': "Discount",
			'account_id': account_id,
			'price_unit': discountNominal or 0.0,
			'quantity': 1,
			'invoice_line_tax_id': invoiceLineTaxId
		}
	def _makeInvoiceLine(self,cr,uid,taxesId,acc_discount_id,discountNominal,context=None):
		if context is None:
			context = {}

		product_discount = False
		obj_product = self.pool.get('product.product').search(cr, uid, [('default_code', '=', 'DISCPEMBELIAN')])
		if obj_product:
			product = self.pool.get('product.product').browse(cr, uid, obj_product)[0]
			product_discount = product.id
		else:
			raise osv.except_osv(_('Information!'),
				_('Please Create Master Product dengan Part Number DISCPEMBELIAN'))

		journal_obj = self.pool.get('account.journal')
		inv_obj = self.pool.get('account.invoice')
		inv_line_obj = self.pool.get('account.invoice.line')

		invoiceLineTaxId = taxesId
		inv_line_discount_data = self._prepare_inv_line_for_discount(cr, uid, acc_discount_id, discountNominal, invoiceLineTaxId, product_discount, context=context)
		
		return inv_line_obj.create(cr, uid, inv_line_discount_data, context=context)
		

	def action_invoice_create(self, cr, uid, ids, context=None):
		
		"""Generates invoice for given ids of purchase orders and links that invoice ID to purchase order.
		:param ids: list of ids of purchase orders.
		:return: ID of created invoice.
		:rtype: int
		"""
		print "coba testttttttttttttttttttttttttttttttttttttttttttttttttttttttt"
		if context is None:
			context = {}
		journal_obj = self.pool.get('account.journal')
		inv_obj = self.pool.get('account.invoice')
		inv_line_obj = self.pool.get('account.invoice.line')

		res = False
		uid_company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
		for order in self.browse(cr, uid, ids, context=context):
			context.pop('force_company', None)
			if order.company_id.id != uid_company_id:
				#if the company of the document is different than the current user company, force the company in the context
				#then re-do a browse to read the property fields for the good company.
				context['force_company'] = order.company_id.id
				order = self.browse(cr, uid, order.id, context=context)
			pay_acc_id = order.partner_id.property_account_payable.id
			journal_ids = journal_obj.search(cr, uid, [('type', '=', 'purchase'), ('company_id', '=', order.company_id.id)], limit=1)
			if not journal_ids:
				raise osv.except_osv(_('Error!'),
					_('Define purchase journal for this company: "%s" (id:%d).') % (order.company_id.name, order.company_id.id))

			# generate invoice line correspond to PO line and link that to created invoice (inv_id) and PO line
			inv_lines = []
			# state for check is all has vat in
			allWithPPN = True
			listInvPPN = {"vat":[],"nonVat":[]}
			for po_line in order.order_line:
				
				if not po_line.taxes_id:
					allWithPPN=False
					listInvPPN["nonVat"].append(po_line.id)
				else:
					listInvPPN["vat"].append(po_line.id)

				acc_id = self._choose_account_from_po_line(cr, uid, po_line, context=context)
				inv_line_data = self._prepare_inv_line(cr, uid, acc_id, po_line, context=context)
				inv_line_id = inv_line_obj.create(cr, uid, inv_line_data, context=context)
				inv_lines.append(inv_line_id)

				po_line.write({'invoice_lines': [(4, inv_line_id)]}, context=context)
			
			# START AUTOMATIC CONVERT DISCOUNT TO NOMINAL
			acc_discount_id=271 #DISCOUNT PEMBELIAN
			# IF ALL LINE WITH PPN THEN WE JUST ONLY CREATE 1 INVOICE LINE
			
			if order.total_discount != 0.0:

				if allWithPPN:
					invoiceLineTaxId = [(6,0,[1])]
					# inv_line_discount_data = self._prepare_inv_line_for_discount(cr, uid, acc_discount_id, (0-order.total_discount), invoiceLineTaxId, context=context)
					# inv_line_discount_id = inv_line_obj.create(cr, uid, inv_line_discount_data, context=context)
					
					inv_line_discount_id = self._makeInvoiceLine(cr,uid,invoiceLineTaxId,acc_discount_id,(0-order.total_discount))
					inv_lines.append(inv_line_discount_id)


				else:
					totalDiscount2 = {"vat":0,"nonVat":0}
					# LOOP EACH LINE WITH VAT
					for discountWithVAT in self.pool.get('purchase.order.line').browse(cr,uid,listInvPPN['vat']):
						# COUNT
						totalDiscount2['vat']+= (discountWithVAT.price_unit*discountWithVAT.product_qty)-discountWithVAT.price_subtotal
					# MAKE INVOICE LINE
					totalDiscount2['vat']= 0 - totalDiscount2['vat']
					if totalDiscount2['vat']!=0:
						inv_line_discount_id = self._makeInvoiceLine(cr,uid,[(6,0,[1])],acc_discount_id,totalDiscount2['vat'])
						inv_lines.append(inv_line_discount_id)

					for discountWithoutVAT in self.pool.get('purchase.order.line').browse(cr,uid,listInvPPN['nonVat']):
						
						totalDiscount2['nonVat']+=(discountWithoutVAT.price_unit*discountWithoutVAT.product_qty)-discountWithoutVAT.price_subtotal

					totalDiscount2['nonVat']= 0 - totalDiscount2['nonVat']
					if totalDiscount2['nonVat'] != 0:
						inv_line_discount_id = self._makeInvoiceLine(cr,uid,[],acc_discount_id,totalDiscount2['nonVat'])
						inv_lines.append(inv_line_discount_id)

			# get invoice data and create invoice
			inv_data = {
				'name': order.partner_ref or order.name,
				'reference': order.partner_ref or order.name,
				'account_id': pay_acc_id,
				'type': 'in_invoice',
				'partner_id': order.partner_id.id,
				'currency_id': order.pricelist_id.currency_id.id,
				'journal_id': len(journal_ids) and journal_ids[0] or False,
				'invoice_line': [(6, 0, inv_lines)],
				'origin': order.name,
				'fiscal_position': order.fiscal_position.id or False,
				'payment_term': order.payment_term_id.id or False,
				'company_id': order.company_id.id,
				'group_id':False
			}
			inv_id = inv_obj.create(cr, uid, inv_data, context=context)
			
			inv_obj.button_compute(cr, uid, [inv_id], context=context, set_total=True)

			# Link this new invoice to related purchase order
			order.write({'invoice_ids': [(4, inv_id)]}, context=context)
			res = inv_id
		return res
		# return  False

# END FOR FINANCE DISCOUNT AMOUNT


# class MergePickings(osv.osv):
# 	_inherit='merge.pickings'



# FOR FINANCE DISCOUNT AMOUNT
class account_invoice_line(osv.osv):
	def replace_discount(self,cr,uid,ids,qty,price, disc):
		
		discount = ((qty*price)*disc)/100.0
		return {'value':{ 'amount_discount':discount} }
	def _amount_line(self, cr, uid, ids, prop, unknow_none, unknow_dict):
		
		# TEST AJA lagi
		res = {}
		res = super(account_invoice_line,self)._amount_line(cr,uid,ids,prop,unknow_none,unknow_dict)
		# tax_obj = self.pool.get('account.tax')
		# cur_obj = self.pool.get('res.currency')
		# for line in self.browse(cr, uid, ids):
		# 	if line.discount!=0.0:
		
		# 		price = line.price_unit * (1-(line.discount or 0.0)/100.0)
		# 	elif line.amount_discount!=0.0:
		
		# 		price = line.price_unit - (line.amount_discount/line.quantity)
		# 	else:
		# 		price = line.price_unit
			
			
		# 	taxes = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, price, line.quantity, product=line.product_id, partner=line.invoice_id.partner_id)
		# 	res[line.id] = taxes['total']
		# 	if line.invoice_id:
		# 		cur = line.invoice_id.currency_id
		# 		res[line.id] = cur_obj.round(cr, uid, cur, res[line.id])
		
		return res


	_name='account.invoice.line'
	_inherit='account.invoice.line'
	_columns={
		'amount_discount':fields.float('Amount Discount',required=False),
		'price_subtotal': fields.function(_amount_line, string='Amount', type="float",digits_compute= dp.get_precision('Account'), store=True),
		'state':fields.related('invoice_id','state',type='char',store=False,string="State"),
	}


	def move_line_get_item(self, cr, uid, line, context=None):

		if line.name:
			a = line.name
		else:
			a = '[ ' + line.product_id.default_code + ' ] ' + line.product_id.name 

		desc = a.split('\n')[0][:64]

		return {
			'type':'src',
			'name': desc,
			'price_unit':line.price_unit,
			'quantity':line.quantity,
			'price':line.price_subtotal,
			'account_id':line.account_id.id,
			'product_id':line.product_id.id,
			'uos_id':line.uos_id.id,
			'account_analytic_id':line.account_analytic_id.id,
			'taxes':line.invoice_line_tax_id,
		}

		
account_invoice_line()

# INHERIT CLASS FOR ACCOUNT BANK STATEMENT LINE
# For Bank Statment Size
class account_bank_statement_line(osv.osv):
	_name = "account.bank.statement.line"
	_inherit = "account.bank.statement.line"
	_columns={
		'ref': fields.text('Reference'),
		'po_id':fields.many2one('purchase.order',string="PO"),
	}

class wizard_suplier_first_payment(osv.osv_memory):
	_name = 'wizard.supplier.first.payment'
	_description = 'Supplier DP with Bank Statement'
	_columns = {
		'name':fields.char('Reference',required=True),
		'po_id':fields.many2one('purchase.order','PO No',required=True),
		'journal_id': fields.many2one('account.journal', 'Journal', required=True,domain=[('type','=','bank')]),
		'payment_date':fields.date('Date',required=True),
		'period_id': fields.many2one('account.period', 'Period', required=True),
		'obi':fields.char('OBI',required=True),
		'ref':fields.text('Reference'),
		'voucher_code':fields.char('No Cek/Giro'),
		'method':fields.selection([('cash','Cash'),('cek','Cheques'),('giro','Giro'),('transfer','Transfer')],string="Payment Method",required=True),
		'rate':fields.float('BI Rate'),
		'partner_id': fields.many2one('res.partner',required=True,string="Supplier",domain=[('supplier','=',True)]),
		'account_id':fields.many2one('account.account',string="Account",required=True),
		'amount':fields.float(string="Amount",required=True),
	}
	_defaults={
		'account_id':69
	}

	def check(self,cr,uid,values,context=None):
		val = self.browse(cr, uid, values)[0]

		acc_bs = self.pool.get('account.bank.statement')
		acc_bs_line = self.pool.get('account.bank.statement.line')

		po = self.pool.get('purchase.order')

		acc1 = acc_bs.create(cr,uid,{
			'name' : val.name,
			'date' : val.payment_date,
			'journal_id' : val.journal_id.id,
			
			'period_id' : val.period_id.id
		},context)
		amount = val.amount
		if amount > 0:
			amount = -(val.amount)

		acc11 = acc_bs_line.create(cr,uid,{
			'date' : val.payment_date,
			'name' : val.obi,
			'ref' : val.ref,
			'code_voucher' : val.voucher_code,
			'method' : val.method,
			'kurs' : val.rate,
			'partner_id' : val.partner_id.id,
			'type':'supplier',
			'sequence':0,
			'account_id' : val.account_id.id,
			'amount' : amount,
			'po_id' : val.po_id.id,
			'statement_id':acc1
		})

		dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'view_bank_statement_form')
		return {
			'view_mode': 'form',
			'view_id': view_id,
			'view_type': 'form',
			'view_name':'account.bank.statement.form',
			'res_model': 'account.bank.statement',
			'type': 'ir.actions.act_window',
			'target': 'current',
			'res_id':acc1,
			'domain': "[('id','=',"+str(acc1)+")]",
		}
		
	def on_change_po_id(self,cr,uid,ids,po_id):
		res = {}
		po_obj = self.pool.get('purchase.order')
		browse = po_obj.browse(cr,uid,po_id)
		

		return {
			'value':{
				'partner_id':browse.partner_id.id
			}
		}
	

class account_invoice(osv.osv):
	def actionPrintCustInv(self,cr,uid,ids,context=None):
		searchConf = self.pool.get('ir.config_parameter').search(cr, uid, [('key', '=', 'base.print')], context=context)
		browseConf = self.pool.get('ir.config_parameter').browse(cr,uid,searchConf,context=context)[0]
		urlTo = str(browseConf.value)+"account-invoice/print-invoice&id="+str(ids[0])+"&uid="+str(uid)
		
		for browse in self.browse(cr,uid,ids):
			if browse.partner_id.npwp == '11111111111111111111':
				raise osv.except_osv(_('Error!'),_('NPWP Customer = '+browse.partner_id.npwp+'\r\nTolong Update NPWP terlebih dahulu. Jika Customer ini tidak mempunyai NPWP tolong Update NPWP menjadi 00.000.000.0-000.000'))
		return {
			'type'	: 'ir.actions.client',
			'target': 'new',
			'tag'	: 'print.out',
			'params': {
				'redir'	: urlTo
			},
		}

	def actionPrintFaktur(self,cr,uid,ids,context=None):
		searchConf = self.pool.get('ir.config_parameter').search(cr, uid, [('key', '=', 'base.print')], context=context)
		browseConf = self.pool.get('ir.config_parameter').browse(cr,uid,searchConf,context=context)[0]
		urlTo = str(browseConf.value)+"account-invoice/print&id="+str(ids[0])+"&uid="+str(uid)

		for browse in self.browse(cr,uid,ids):
			if browse.partner_id.npwp == '11111111111111111111':
				raise osv.except_osv(_('Error!'),_('NPWP Customer = '+browse.partner_id.npwp+'\r\nTolong Update NPWP terlebih dahulu. Jika Customer ini tidak mempunyai NPWP tolong Update NPWP menjadi 00.000.000.0-000.000'))
		return {
			'type'	: 'ir.actions.client',
			'target': 'new',
			'tag'	: 'print.out',
			'params': {
				# 'id'	: ids[0],
				'redir'	: urlTo
			},
		}

	def actionPrintKwitansi(self,cr,uid,ids,context=None):
		searchConf = self.pool.get('ir.config_parameter').search(cr, uid, [('key', '=', 'base.print')], context=context)
		browseConf = self.pool.get('ir.config_parameter').browse(cr,uid,searchConf,context=context)[0]
		urlTo = str(browseConf.value)+"account-invoice/print-kwitansi&id="+str(ids[0])+"&uid="+str(uid)
		return {
			'type'	: 'ir.actions.client',
			'target': 'new',
			'tag'	: 'print.out',
			'params': {
				# 'id'	: ids[0],
				'redir'	: urlTo
			},
		}


	def action_to_tax_replacement(self,cr,uid,ids,context={}):
		res = False
		invs = self.browse(cr,uid,ids,context=context)
		newids = []
		for inv in invs:
			picking_ids = [(6,0, [pick.id]) for pick in inv.picking_ids]
			# res = [(0,0,self._im_line_preparation(cr,uid,line)) for line in request.lines if (line.qty-line.processed_item_qty) > 0]
			invoice_lines =  [(0, 0, self.pool.get('account.invoice.line').copy_data(cr,uid,line.id,{'invoice_id':False},context=context)) for line in inv.invoice_line]

			

			# newid = self.copy(cr,uid,inv.id,default=default,context=context)
			# override copy new
			copy_new = self.copy_data(cr, uid, inv.id, context=context, default={'invoice_line':invoice_lines,'picking_ids':picking_ids})
			
			newid = self.create(cr,uid,copy_new,context=context)
			
			# raise osv.except_osv(_('Error!'),_('Tes'))
			newids = [newid]
			newInv = self.browse(cr,uid,newid,context=context)
			
			fp_no = newInv.faktur_pajak_no[0:2]+'1.'+newInv.faktur_pajak_no[4:20]

			
			# self.write(cr,uid,newid,{'faktur_pajak_no':fp_no})
			# canceling old invoice
			self.write(cr,uid,[inv.id],{'state':'cancel'})
			# new faktur  number
			self.write(cr,uid,newid,{'faktur_pajak_no':fp_no,'tax_invoice_origin_id':inv.id})

		mod_obj = self.pool.get('ir.model.data')
		res = mod_obj.get_object_reference(cr, uid, 'account', 'invoice_form')
		res_id = res and res[1] or False,

		return {
			'name': _('Customer Invoices'),
			'view_type': 'form',
			'view_mode': 'form',
			'view_id': [res_id],
			'res_model': 'account.invoice',
			'context': "{'type':'out_invoice'}",
			'type': 'ir.actions.act_window',
			'nodestroy': True,
			'target': 'current',
			'res_id': newids and newids[0] or False,
		}
		
		# return res

	_name='account.invoice'
	_inherit='account.invoice'
	_columns={
		# 'total_discount':fields.function(_amount_all_main,string='Total Discount',required=False,store=False),
		# 'total_discount':fields.function(_get_total_discount,string='Total Discount',required=False,store=False),
		'payment_for':fields.selection([('dp','DP'),('completion','Completion')],string="Payment For",required=False),
		'print_all_taxes_line':fields.boolean(string="Print All Taxes Item ?",required=False),
		'faktur_address':fields.many2one('res.partner',string="Faktur Address",required=False),
		'group_id':fields.many2one('group.sales',required=True,string="Sale Group",domain=[('is_main_group','=',True)]),
		'tax_invoice_origin_id': fields.many2one('account.invoice',string="Invoice Origin",required=False, ondelete='RESTRICT',onupdate='RESTRICT'),
		'dp_percentage': fields.float(string='DP/Termin Percentage',required=False),
	}
	_defaults={
		'print_all_taxes_line':True,
		'dp_percentage':0,
	}

	def action_cancel(self,cr,uid,ids,context={}):
		ir_model_data_group = self.pool.get('ir.model.data').search(cr,uid,[('model','=','res.groups'),('name','=','group_customer_invoice_administrator'),('module','=','sbm_inherit')],context=context)
		ir_model_data_group_finance = self.pool.get('ir.model.data').search(cr,uid,[('model','=','res.groups'),('name','=','group_account_manager'),('module','=','account')],context=context)
		if ir_model_data_group or ir_model_data_group_finance:
			data = self.pool.get('ir.model.data').browse(cr,uid,ir_model_data_group[0],context=context)
			data_finance = self.pool.get('ir.model.data').browse(cr,uid,ir_model_data_group_finance[0],context=context)
			res_id = data.res_id
			res_id_finance = data_finance.res_id
			# check if user in group customer invoice administrator ?
			# only customer invoice administrator can cancel the invoice
			group = self.pool.get('res.groups').search(cr,uid,[('id','=',res_id),('users','in',uid)])
			group_finance = self.pool.get('res.groups').search(cr,uid,[('id','=',res_id_finance),('users','in',uid)])
			
			if group or group_finance:
				return super(account_invoice,self).action_cancel(cr,uid,ids,context)
			else:
				raise osv.except_osv(_('Error!'),_('Your\'re not Authorized to Canceling Invoice!'))
			
		return False

	def getGroupByUser(self,cr,uid,ids,user_id,context={}):
		user = self.pool.get('res.users').browse(cr,uid,user_id,context)

		group_id = False
		groupDomain = [("is_main_group","=",True)]

		main_groups = self.pool.get('group.sales').search(cr,uid,[('is_main_group','=',True)])
		user = self.pool.get('res.users').browse(cr,uid,user_id,context)
		group_id = False
		groups_sale_lines = self.pool.get('group.sales.line').search(cr,uid,[('name','=',user_id),('kelompok_id','in',main_groups)])
		

		if len(groups_sale_lines) == 1:
			if user.kelompok_id:
				
				if user.kelompok_id.parent_id:
					group_id = user.kelompok_id.parent_id.id
				else:
					if user.kelompok_id.is_main_group:
						group_id = user.kelompok_id.id
					else:
						group_id = False
		res = {
			'value':{
				'group_id':group_id,
			}
		}
		return res


class account_invoice_tax(osv.osv):
	def compute(self, cr, uid, invoice_id, context=None):
		
		# tax_grouped = super(account_invoice_tax,self).compute(cr,uid,invoice_id,context=context)
		tax_grouped = {}
		
		tax_obj = self.pool.get('account.tax')
		cur_obj = self.pool.get('res.currency')
		inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
		cur = inv.currency_id
		company_currency = self.pool['res.company'].browse(cr, uid, inv.company_id.id).currency_id.id
		dec_precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')


		for line in inv.invoice_line:
			if line.discount!=0.0:
				
				price = line.price_unit * (1-(line.discount or 0.0)/100.0)
			elif line.amount_discount!=0.0:
				
				price = line.price_unit - (line.amount_discount/line.quantity)
			else:
				price = line.price_unit
			for tax in tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, price, line.quantity, line.product_id, inv.partner_id)['taxes']:
				val={}
				val['invoice_id'] = inv.id
				val['name'] = tax['name']
				val['amount'] = tax['amount']
				val['manual'] = False
				val['sequence'] = tax['sequence']
				val['base'] = round(tax['price_unit'] * line['quantity'],dec_precision)

				if inv.type in ('out_invoice','in_invoice'):
					val['base_code_id'] = tax['base_code_id']
					val['tax_code_id'] = tax['tax_code_id']
					
					val['base_amount'] = round(val['base'] * tax['base_sign'],dec_precision)

					
					val['tax_amount'] = math.floor(val['amount'] * tax['tax_sign'])
					val['account_id'] = tax['account_collected_id'] or line.account_id.id
					val['account_analytic_id'] = tax['account_analytic_collected_id']
				else:
					val['base_code_id'] = tax['ref_base_code_id']
					val['tax_code_id'] = tax['ref_tax_code_id']
					val['base_amount'] = round(val['base'] * tax['ref_base_sign'], dec_precision)
					val['tax_amount'] = round(val['amount'] * tax['ref_tax_sign'],dec_precision)
					val['account_id'] = tax['account_paid_id'] or line.account_id.id
					val['account_analytic_id'] = tax['account_analytic_paid_id']

				key = (val['tax_code_id'], val['base_code_id'], val['account_id'], val['account_analytic_id'])
				if not key in tax_grouped:
					tax_grouped[key] = val
				else:
					tax_grouped[key]['amount'] += val['amount']
					tax_grouped[key]['base'] += val['base']
					tax_grouped[key]['base_amount'] += val['base_amount']
					tax_grouped[key]['tax_amount'] += val['tax_amount']

		for t in tax_grouped.values():
			t['base'] = round(t['base'],dec_precision)
			t['amount'] = round(t['amount'],dec_precision)
			t['base_amount'] = round(t['base_amount'],dec_precision)
			t['tax_amount'] = round(t['tax_amount'],dec_precision)
		return tax_grouped

	_name='account.invoice.tax'
	_inherit='account.invoice.tax'

class GroupSales(osv.osv):
	_inherit = 'group.sales'
	_columns = {
		'desc':fields.char('Short Description',required=False),
		'is_main_group':fields.boolean('Is a Main Group', required=False),
		'parent_id':fields.many2one('group.sales',string="Parent Group",required=False,ondelete="restrict",onupdate="cascade")
	}
	_rec_name = 'desc';
	_defaults = {
		'is_main_group':False,
	}
	
class SaleOrder(osv.osv):
	_inherit = 'sale.order'
	_columns = {
		'group_id':fields.many2one('group.sales',required=True,string="Sale Group"),
	}

	def action_button_confirm(self, cr, uid, ids, context=None):
		data = self.browse(cr,uid,ids,context)[0]
		if data.pricelist_id.name == 'IDR':
			# if idr then check amount total of order
			# if amount total of order < 1 hundred thousand rupiah then block it
			if data.amount_total < 100000 and data.amount_total > 0:
				raise osv.except_osv(_('Error!'),_('Tidak bisa menjual dengan nilai total penjualan dibawah IDR 100.000,-'))
		return super(SaleOrder, self).action_button_confirm(cr, uid, ids, context)

	def _prepare_invoice(self, cr, uid, order, lines, context=None):
		
		"""Prepare the dict of values to create the new invoice for a
		   sales order. This method may be overridden to implement custom
		   invoice generation (making sure to call super() to establish
		   a clean extension chain).

		   :param browse_record order: sale.order record to invoice
		   :param list(int) line: list of invoice line IDs that must be
								  attached to the invoice
		   :return: dict of value to create() the invoice
		"""

		order_currency_id = order.pricelist_id.currency_id.id

		user = self.pool.get('res.users').browse(cr,uid,uid,context=context)

		if order_currency_id != user.company_id.currency_id.id:
			cr.execute('SELECT "rating" FROM "res_currency_rate" WHERE "currency_id" = %s ORDER BY "name" DESC limit 1',(order_currency_id,))
			today_rate = cr.fetchone()[0]
		else:
			today_rate = 1.0


		if context is None:
			context = {}
		journal_ids = self.pool.get('account.journal').search(cr, uid,
			[('type', '=', 'sale'), ('company_id', '=', order.company_id.id)],
			limit=1)
		if not journal_ids:
			raise osv.except_osv(_('Error!'),
				_('Please define sales journal for this company: "%s" (id:%d).') % (order.company_id.name, order.company_id.id))
		invoice_vals = {
			'name': order.client_order_ref or '',
			'origin': order.name,
			'type': 'out_invoice',
			'reference': order.client_order_ref or order.name,
			'account_id': order.partner_id.property_account_receivable.id,
			'partner_id': order.partner_invoice_id.id,
			'journal_id': journal_ids[0],
			'invoice_line': [(6, 0, lines)],
			'currency_id': order.pricelist_id.currency_id.id,
			'comment': order.note,
			'payment_term': order.payment_term and order.payment_term.id or False,
			'fiscal_position': order.fiscal_position.id or order.partner_id.property_account_position.id,
			'date_invoice': context.get('date_invoice', False),
			'company_id': order.company_id.id,
			'user_id': order.user_id and order.user_id.id or False,
			'group_id':order.group_id.id or False,
			'user_id': order.user_id.id,
			'pajak': today_rate,
		}
		
		# Care for deprecated _inv_get() hook - FIXME: to be removed after 6.1
		invoice_vals.update(self._inv_get(cr, uid, order, context=context))
		return invoice_vals


	def getGroupByUser(self,cr,uid,ids,user_id,context={}):
		user = self.pool.get('res.users').browse(cr,uid,user_id,context)

		group_id = False
		groupDomain = [("is_main_group","=",True)]

		main_groups = self.pool.get('group.sales').search(cr,uid,[('is_main_group','=',True)])
		user = self.pool.get('res.users').browse(cr,uid,user_id,context)
		group_id = False
		groups_sale_lines = self.pool.get('group.sales.line').search(cr,uid,[('name','=',user_id),('kelompok_id','in',main_groups)])
		
		if len(groups_sale_lines) == 1:
			if user.kelompok_id:
				
				if user.kelompok_id.parent_id:
					group_id = user.kelompok_id.parent_id.id
				else:
					if user.kelompok_id.is_main_group:
						group_id = user.kelompok_id.id
					else:
						group_id = False
		res = {
			'value':{
				'group_id':group_id,
			}
		}
		return res


class SaleOrderLine(osv.osv):
	def replace_discount(self,cr,uid,ids,qty,price, disc):

		subtotal = qty*price
		nilai = (subtotal*disc)/100.00
		print nilai,'------------------'
		return {'value':{ 'discount_nominal':nilai} }


	def on_change_product_uom_qty(self,cr,uid,ids,product_uom_qty,price_unit,discount):
		res = {}
		get_discount = self.replace_discount(cr,uid,ids,product_uom_qty,price_unit,discount)
		discount_nominal = get_discount['value']['discount_nominal']


		res['value'] = {'discount_nominal': discount_nominal,'product_uos_qty':product_uom_qty}

		return res

	_name = 'sale.order.line'
	_inherit = 'sale.order.line'
	_columns = {
		'product_id': fields.many2one('product.product', 'Product', domain=[('sale_ok', '=', True)], change_default=True, required=True),
	}
	_order = 'sequence ASC'

SaleOrderLine()

class AccountBankStatement(osv.osv):
	def _getSubTotal(self, cr, uid, ids, name, arg, context=None):
		res = {}

		accounts= self.browse(cr, uid, ids, context=context)
		for account in accounts:
			# dis[order.id]=order.amount_bruto-order.amount_untaxed
			res[account.id] = 0
			
			for line in account.line_ids:
				res[account.id] += line.amount
				
		return res

	_name = 'account.bank.statement'
	_inherit = 'account.bank.statement'
	_columns = {
		'subtotal':fields.function(_getSubTotal,string='Total',required=False,store=False),
	}

# class OrderPreparation(osv.osv):
# 	_inherit = 'order.preparation'
# 	_name = 'order.preparation'
# 	

class DeliveryNote(osv.osv):
	
	_description = 'Delivery Note'
	_name = 'delivery.note'
	_inherit = ['delivery.note','mail.thread']
	_track = {
		'partner_shipping_id':{

		},
		'delivery_date':{

		}
	}

class SerialNumber(osv.osv):
	_description = 'Serial Number'
	_name = 'stock.production.lot'
	_inherit= 'stock.production.lot'
	_columns = {
		'desc':fields.text('Description'),
		'exp_date':fields.date('Exp Date'),
	}

class split_in_production_lot(osv.osv_memory):
	_name = "stock.move.split"
	_inherit = "stock.move.split"
	_description = "Stock move Split"

	def split_lot(self, cr, uid, ids, context=None):
		""" To split a lot"""
		if context is None:
			context = {}
		res = self.split(cr, uid, ids, context.get('active_ids'), context=context)
		return {'type': 'ir.actions.act_window_close'}

	def split(self, cr, uid, ids, move_ids, context=None):
		""" To split stock moves into serial numbers

		:param move_ids: the ID or list of IDs of stock move we want to split
		"""
		if context is None:
			context = {}
		assert context.get('active_model') == 'stock.move',\
			 'Incorrect use of the stock move split wizard'
		inventory_id = context.get('inventory_id', False)
		prodlot_obj = self.pool.get('stock.production.lot')
		inventory_obj = self.pool.get('stock.inventory')
		move_obj = self.pool.get('stock.move')
		new_move = []
		for data in self.browse(cr, uid, ids, context=context):
			for move in move_obj.browse(cr, uid, move_ids, context=context):
				move_qty = move.product_qty
				quantity_rest = move.product_qty
				uos_qty_rest = move.product_uos_qty
				new_move = []
				if data.use_exist:
					lines = [l for l in data.line_exist_ids if l]
				else:
					lines = [l for l in data.line_ids if l]
				total_move_qty = 0.0
				for line in lines:
					quantity = line.quantity
					total_move_qty += quantity
					if total_move_qty > move_qty:
						raise osv.except_osv(_('Processing Error!'), _('Serial number quantity %d of %s is larger than available quantity (%d)!') \
								% (total_move_qty, move.product_id.name, move_qty))
					if quantity <= 0 or move_qty == 0:
						continue
					quantity_rest -= quantity
					uos_qty = quantity / move_qty * move.product_uos_qty
					uos_qty_rest = quantity_rest / move_qty * move.product_uos_qty
					if quantity_rest < 0:
						quantity_rest = quantity
						self.pool.get('stock.move').log(cr, uid, move.id, _('Unable to assign all lots to this move!'))
						return False
					default_val = {
						'product_qty': quantity,
						'product_uos_qty': uos_qty,
						'state': move.state
					}
					if quantity_rest > 0:
						current_move = move_obj.copy(cr, uid, move.id, default_val, context=context)
						if inventory_id and current_move:
							inventory_obj.write(cr, uid, inventory_id, {'move_ids': [(4, current_move)]}, context=context)
						new_move.append(current_move)

					if quantity_rest == 0:
						current_move = move.id
					prodlot_id = False
					if data.use_exist:
						prodlot_id = line.prodlot_id.id
						desc = line.prodlot_id.desc
						move_obj.write(cr, uid, [current_move], {'prodlot_id': prodlot_id, 'name' : desc, 'state':move.state})
					if not prodlot_id:
						prodlot_id = prodlot_obj.create(cr, uid, {
							'name': line.name,
							'desc':line.desc,
							'exp_date':line.exp_date,
							'product_id': move.product_id.id},
						context=context)

						move_obj.write(cr, uid, [current_move], {'prodlot_id': prodlot_id, 'state':move.state})

					move_obj.write(cr, uid, [current_move], {'prodlot_id': prodlot_id, 'state':move.state})

					update_val = {}
					if quantity_rest > 0:
						update_val['product_qty'] = quantity_rest
						update_val['product_uos_qty'] = uos_qty_rest
						update_val['state'] = move.state
						move_obj.write(cr, uid, [move.id], update_val)

		return new_move

split_in_production_lot()


class stock_move_split_lines_exist(osv.osv_memory):
	_name = "stock.move.split.lines"
	_inherit = "stock.move.split.lines"
	_description = "Stock move Split lines"


	def name_get(self, cr, uid, ids, context=None):
		if not ids:
			return []
		reads = self.read(cr, uid, ids, ['name', 'prefix', 'ref'], context)
		res = []
		for record in reads:
			name = record['name']
			prefix = record['prefix']
			if prefix:
				name = prefix + '/' + name
			if record['ref']:
				name = '%s [%s]' % (name, record['ref'])
			res.append((record['id'], name))
		return res

	def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
		args = args or []
		ids = []
		if name:
			ids = self.search(cr, uid, [('prefix', '=', name)] + args, limit=limit, context=context)
			if not ids:
				ids = self.search(cr, uid, [('name', operator, name)] + args, limit=limit, context=context)
		else:
			ids = self.search(cr, uid, args, limit=limit, context=context)
		return self.name_get(cr, uid, ids, context)
		
	def _get_stock(self, cr, uid, ids, context=None):
		""" Gets stock of products for locations
		@return: Dictionary of values
		"""
		if context is None:
			context = {}
		if 'location_id' not in context:
			locations = self.pool.get('stock.location').search(cr, uid, [('usage', '=', 'internal')], context=context)
		else:
			locations = context['location_id'] and [context['location_id']] or []

		if isinstance(ids, (int, long)):
			ids = [ids]

		res = {}.fromkeys(ids, 0.0)
		if locations:
			cr.execute('''select
					prodlot_id,
					sum(qty)
				from
					stock_report_prodlots
				where
					location_id IN %s and prodlot_id IN %s group by prodlot_id''',(tuple(locations),tuple(ids),))
			res.update(dict(cr.fetchall()))

		return 100

	def _stock_search(self, cr, uid, obj, name, args, context=None):
		""" Searches Ids of products
		@return: Ids of locations
		"""
		locations = self.pool.get('stock.location').search(cr, uid, [('usage', '=', 'internal')])
		cr.execute('''select
				prodlot_id,
				sum(qty)
			from
				stock_report_prodlots
			where
				location_id IN %s group by prodlot_id
			having  sum(qty) '''+ str(args[0][1]) + str(args[0][2]),(tuple(locations),))
		res = cr.fetchall()
		ids = [('id', 'in', map(lambda x: x[0], res))]
		return ids

	_columns = {
		'name': fields.char('Serial Number', size=64),
		'quantity': fields.float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure')),
		'wizard_id': fields.many2one('stock.move.split', 'Parent Wizard'),
		'wizard_exist_id': fields.many2one('stock.move.split', 'Parent Wizard (for existing lines)'),
		'prodlot_id': fields.many2one('stock.production.lot', 'Serial Number'),
		'desc':fields.text('Description'),
		'exp_date':fields.date('Exp Date'),
		'stock_available': fields.float('Stock Available'),
	}
	_defaults = {
		'quantity': 0.0,
	}
	def _dumy_getStock(self,cr,uid,ids,prodlot_id,context=None):
		stock = 10
		return stock
	def onchange_lot_id(self, cr, uid, ids, prodlot_id=False, product_qty=False,
						loc_id=False, product_id=False, uom_id=False,context=None):
		if prodlot_id == False:
			return False
		else:
			
			hasil=self.pool.get('stock.production.lot').browse(cr,uid,[prodlot_id])[0]

			if product_qty > hasil.stock_available:
				raise openerp.exceptions.Warning('Stock Available Tidak Mencukupi')
				return {'value':{'quantity':0}}

			return {'value':{'desc':hasil.desc,'exp_date':hasil.exp_date,'stock_available':hasil.stock_available}}
		return self.pool.get('stock.move').onchange_lot_id(cr, uid, [], prodlot_id, product_qty,
						loc_id, product_id, uom_id, context)


# ---------------------------------------------
# OVERRIDE INTERMAL MOVE REDIRECT ON DO PARTIAL
# ---------------------------------------------
class stock_picking(osv.osv):
	_inherit = "stock.picking"
	_name = "stock.picking"
	def do_partial(self, cr, uid, ids, partial_datas, context=None):
		pick = self.browse(cr,uid,ids)
		
		if pick[0].name==False:
			# GENERATE NUMBER
			self.generateSeq(cr,uid,ids,context)
		
		res = super(stock_picking,self).do_partial(cr,uid,ids,partial_datas,context)
		return res
	def generateSeq(self,cr,uid,ids,context=None):
		pick = self.browse(cr,uid,ids)

		if pick[0].name == False:
			newPickName = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking')
			return self.write(cr,uid,ids,{'name':newPickName})
		else:
			raise osv.except_osv(('Error !!!'), ('Can\'t Update Squence'))
			return False


class stock_move(osv.osv):
	
	_inherit = 'stock.move'
	_order = 'no ASC'


class bom(osv.osv):
	def checkUniqueByProduct(self,cr,uid,prod_id):
		objs = self.search(cr,uid,[('product_id', '=', prod_id),('bom_id','=',False)])
		return objs

	def create(self,cr,uid,vals,context=None):
		
		if self.checkUniqueByProduct(cr,uid,vals.get('product_id')):
			res = False
			raise osv.except_osv(('Error !!!'), ('Can\'t Create new BOM, BOM has been Exist!!!'))
		else:
			res = super(bom,self).create(cr,uid,vals,context)
		return res
	_inherit='mrp.bom'

class account_move_line(osv.osv):
	_inherit = "account.move.line"
	_columns={
		'ref': fields.related('move_id', 'ref', string='Reference', type='text', store=True),
		'name': fields.char('Name', required=True),
	}

class PurchaseOrderWithDP(osv.osv):
	_inherit = 'purchase.order'
	_columns = {
		'bank_statement_lines':fields.one2many('account.bank.statement.line','po_id',string="First Payments"),
	}

class AccountVoucher(osv.osv):
	_inherit = 'account.voucher'


#Module Cancel Item in Purchase Order

class ClassName(osv.osv):
	
	def action_cancel_item(self,cr,uid,ids,context=None):
		if context is None:
			context = {}
		
		dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'sbm_inherit', 'wizard_po_cancel_item_form')

		context.update({
			'active_model': self._name,
			'active_ids': ids,
			'active_id': len(ids) and ids[0] or False
		})
		return {
			'view_mode': 'form',
			'view_id': view_id,
			'view_type': 'form',
			'view_name':'wizard_po_cancel_item_form',
			'res_model': 'wizard.po.cancel.item',
			'type': 'ir.actions.act_window',
			'target': 'new',
			'context': context,
			'nodestroy': True,
		}
	_inherit = 'purchase.order'

class WizardPOCancelItem(osv.osv_memory):

	def default_get(self, cr, uid, fields, context=None):
		
		if context is None: context = {}
		po_ids = context.get('active_ids', [])
		active_model = context.get('active_model')
		res = super(WizardPOCancelItem, self).default_get(cr, uid, fields, context=context)
		if not po_ids or len(po_ids) != 1:
			# Partial Picking Processing may only be done for one picking at a time
			return res
		po_id, = po_ids
		if po_id:
			res.update(po_id=po_id)
			po = self.pool.get('purchase.order').browse(cr, uid, po_id, context=context)
			linesData = []
			linesData += [self._load_po_line(cr, uid, l) for l in po.order_line if l.state not in ('done','cancel')]
			res.update(lines=linesData)
		
		return res

	def _load_po_line(self, cr, uid, line):
		po_item = {
			'line_id'			: line.id,
			'product_id'		: line.product_id.id,
			'description'		: line.name,
			'uom'				: line.product_uom.id,
			'qty'				: line.product_qty,
			'unit_price'		: line.price_unit,
			'discount_amount'	: line.discount_nominal,
			'discount_percent'	: line.discount,
			'subtotal'			: line.price_subtotal,
		}
		
		return po_item

	def request_cancel_item(self,cr,uid,ids,context=None):
		
		data = self.browse(cr,uid,ids,context)[0]

		polc = self.pool.get('purchase.order.line.cancel')
		# we need to check INVOICES
		# call po
		po = data.po_id
		inv_ids=[] #INVOICE WHERE STATE NOT DRAFT OR CANCEL
		inv_ids+= [self.pool.get('account.invoice').browse(cr,uid,invoice.id,context) for invoice in po.invoice_ids if invoice.state not in ('draft','cancel')]
		
		if len(po.order_line) == len(data.lines):
			raise osv.except_osv(('Error !!!'),('Tidak diperbolehkan mencancel semua item..!!Silahkan mengcancel PO!'))
		newIds = []
		for line in data.lines:
			cancelItems = {
				'po_id':po.id,
				'po_line_id':line.line_id.id,
				'product_id':line.product_id.id,
				'description':line.description,
				'qty':line.qty,
				'uom':line.uom.id,
				'unit_price':line.unit_price,
				'discount_amount':line.discount_amount,
				'discount_percent':line.discount_percent,
				'subtotal':line.subtotal,
				'state':'draft',
				'note':data.note,
			}
			# make sure po line id is unique
			check = self.pool.get('purchase.order.line.cancel').search(cr,uid,[('po_line_id','=',line.line_id.id)])
			if check:
				raise osv.except_osv(('Error !!!'),('TIdak bisa mencancel item "',str(line.product_id.name),'"..!!'))
			newIds+=[polc.create(cr,uid,cancelItems,context)]

		# redir
		dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'sbm_inherit', 'view_po_line_cancel_tree')

		return {
			'view_mode': 'tree',
			'view_id': view_id,
			'view_type': 'form',
			'view_name':'view_po_line_cancel_tree',
			'res_model': 'purchase.order.line.cancel',
			'type': 'ir.actions.act_window',
			'target': 'current',
			# 'domain': "[('id','in',"+newIds+")]",
			'domain': [('id','in',newIds)]
		}



	_name="wizard.po.cancel.item"
	_description="Wizard Cancel Item On P.O"
	_columns = {
		'po_id':fields.many2one('purchase.order',string="Purchase Order",required=True),
		'lines':fields.one2many('wizard.po.cancel.item.line','w_id',string="Lines"),
		'note':fields.text('Note',required=True,help="Reason why item(s) want to be cancel"),
	}
	_rec_name="po_id"


class WizardPOCancelItemLine(osv.osv_memory):
	_name="wizard.po.cancel.item.line"
	_description="Line Wizard Cancel Item On P.O"
	_columns={
		'w_id':fields.many2one('wizard.po.cancel.item',string="Wizard",required=True,ondelete='CASCADE',onupdate='CASCADE'),
		'line_id':fields.many2one('purchase.order.line','Item Line',required=True),
		'product_id':fields.many2one('product.product',string="Product",required=True),
		'description':fields.text('Desc'),
		'qty':fields.float('Qty',required=True),
		'uom':fields.many2one('product.uom',string="Unit of Measure",required=True),
		'unit_price':fields.float('Unit Price'),
		'discount_amount':fields.float('Discount (Amount)'),
		'discount_percent':fields.float('Discount (Percentage)'),
		'subtotal':fields.float('Subtotal'),
	}
	_rec_name = 'w_id'

class PurchaseOrderLineCancel(osv.osv):
	def confirm_cancel(self,cr,uid,ids,context=None):
		if context is None:
			context = {}
		idsToConfirm = context['active_ids']

		# set state to approved
		self.write(cr,uid,idsToConfirm,{'state':'approved','approved_by':uid});
		lineToCancel = []
		poToUpdate = []
		cancel_notes = ""
		for cancelItem in self.browse(cr,uid,idsToConfirm,context):
			line = self.pool.get('purchase.order.line').browse(cr,uid,cancelItem.po_line_id,context)
			
			lineToCancel+=[line.id]
			poToUpdate+=[line.order_id]
			cancelNotes = cancelItem.note
		

		# search stock move
		moveObj = self.pool.get('stock.move')
		movesIdToUnlink = moveObj.search(cr,uid,[('purchase_line_id','in',lineToCancel)])

		self.pool.get('purchase.order.line').unlink(cr,uid,lineToCancel)
		self.pool.get('purchase.order').button_dummy(cr,uid,poToUpdate,context)
		# moveObj.unlink(cr,uid,movesIdToUnlink)
		moveObj.write(cr,uid,movesIdToUnlink,{'state':'cancel','cancel_notes':cancelNotes})



	
	_name = 'purchase.order.line.cancel'
	_description = "Purchase Order Line Cancel"
	
	_columns={
		'po_id':fields.many2one('purchase.order',string="PO No.",required=True,ondelete='CASCADE',onupdate='CASCADE'),
		'po_line_id':fields.integer("Line ID",required=True),
		'product_id':fields.many2one('product.product',string="Product",required=True),
		'description':fields.text('Desc'),
		'qty':fields.float('Qty',required=True),
		'uom':fields.many2one('product.uom',string="Unit of Measure",required=True),
		'unit_price':fields.float('Unit Price'),
		'discount_amount':fields.float('Discount (Amount)'),
		'discount_percent':fields.float('Discount (Percentage)'),
		'subtotal':fields.float('Subtotal'),
		'note':fields.text('Notes',required=True),
		'state':fields.selection([('draft','draft'),('rfa','Waiting Approval'),('approved','Approved')],string="State"),
		'approved_by':fields.many2one('res.users',string="Approved By",ondelete="CASCADE",onupdate='CASCADE'),

	}
	_rec_name = 'po_line_id'
	_default={
		'state':'draft',
	}
	_sql_constraints = [
		('unique_line_id', 'unique(po_line_id)', "Tidak bisa mencancel item yang sama lebih dari 1X!!!"),
	]

class stock_move(osv.osv):
	
	_inherit = 'stock.move'
	_columns = {
		'cancel_notes':fields.text('Cancel Notes',required=False),
		'product_uom': fields.many2one('product.uom', 'Unit of Measure', required=True,states={'done': [('readonly', True)]}),
	}

# Fixing bug min_date on picking when null it will be filled timestamp
# class stockPicking(osv.osv):
# 	_inherit = 'stock.picking'
# 	_columns = {
# 		# 'min_date': fields.function(get_min_max_date, fnct_inv=_set_minimum_date, multi="min_max_date", store=True, type='datetime', string='Scheduled Time', select=1, help="Scheduled time for the shipment to be processed"),
# 		'min_date':fields.datetime(string="Delivery Date",help="Delivered Date shipment",required=False)
# 	}


#START NEW INTERNAL MOVE MODULES DEVELOPMENT
class StockLocation(osv.osv):
	_inherit = 'stock.location'
	_columns = {
		'code':fields.char(size=4,string='Code'),
	}
class InternalMoveRequest(osv.osv):
	STATES = [
		('draft','Draft'),
		('confirmed','Confirmed'),
		('onprocess','On Process'),
		('done','Done'),
		('cancel','Cancel')
	]
	
	def monthToRoman(self,number):
		roman = {
			'01':'I',
			'02':'II',
			'03':'III',
			'04':'IV',
			'05':'V',
			'06':'VI',
			'07':'VII',
			'08':'VIII',
			'09':'IX',
			'10':'X',
			'11':'XI',
			'12':'XII'
		}

		return roman[number]

	def _validateStorage(self,source,dest):

		if source.id==dest.id:
			raise osv.except_osv(_('Error !'),_('Please Check Destination and Source Location, It Can be same as'))

		if dest.code:
			destCode = dest.code
		else:
			raise osv.except_osv(_('Error !'),_('Please define a storage code for '+dest.name))

		return 'MR-'+destCode+'/'+str(time.strftime('%y'))+'/'+str(self.monthToRoman(time.strftime('%m')))
	def _getNewNO(self,cr,uid,ids,context={}):
		# NUMBER FORMAT {code of source location}-{code of destination location}/{2 last year number}/{month in rome}/sequence number
		data = self.browse(cr,uid,ids,context)[0]
		prefix = self._validateStorage(data.source,data.destination)

		if data.name == '/':
			sequence=prefix+'/'+self.pool.get('ir.sequence').get(cr, uid, 'internal.move.request')
		else:
			sequence=data.name

		return sequence

	def _setNewNO(self,cr,uid,ids,context={}):
		return self.write(cr,uid,ids,{'name':self._getNewNO(cr,uid,ids,context)},context)

	def _setState(self,cr,uid,ids,context={},state='draft'):
		return self.write(cr,uid,ids,{'state':state},context)


	def confirmRequest(self,cr,uid,ids,context={}):
		res = {}
		# newNumber = self._getNewNo(cr,uid,ids,context)
		self._setNewNO(cr,uid,ids,context)
		self._setState(cr,uid,ids,context,'confirmed')

		
		return res
	
	# GET STATE CONSTANT
	def getStates(self,cr,uid,context={}):
		return self.STATES

	_name='internal.move.request'
	_inherit = ['mail.thread']
	_columns={
		'name':fields.char('MR No',required=True),
		'source':fields.many2one('stock.location',required=True,string="Source Location"),
		'destination':fields.many2one('stock.location',required=True,string="Destination Location"),
		'due_date':fields.date('Due Date',required=False),
		'manual_pb_no':fields.char('Manual PB NO'),
		'ref_no':fields.char('Ref No'),
		'request_by':fields.many2one('res.users',string="Request By",required=True),
		'notes':fields.text('Notes'),
		'state':fields.selection(STATES,string="State"),
		'lines':fields.one2many('internal.move.request.line','internal_move_request_id',string="Items Request"),
	}

	def SetDraft(self, cr, uid, ids, context=None):
		val = self.browse(cr, uid, ids)[0]
		internal_move = self.pool.get('internal.move')

		cek = internal_move.search(cr,uid,[('internal_move_request_id', '=' ,ids)])

		if cek:
			data = internal_move.browse(cr, uid, cek, context=None)
			for x in data:
				if x.state == 'cancel' or x.state == 'draft':
					return self.write(cr,uid,ids,{'state':'draft'})
				else:
					raise osv.except_osv(('Information !!!'), ('Please Cancel or Set to Draft Internal Move '+ x.name ))
		else:
			return self.write(cr,uid,ids,{'state':'draft'})

		return True

	def _getUID(self,cr,uid,ids,context=None):
		return uid
	def _getName(self,cr,uid,ids,context=None):
		res = '/'
		return res

	_defaults={
		'request_by':_getUID,
		'name':_getName,
		'state':"draft",
	}

class InternalMoveRequestLine(osv.osv):
	def create(self,cr,uid,vals,context={}):
		product = self.pool.get('product.product').browse(cr,uid,vals['product_id'],context)

		vals['uom_id'] = product.uom_id.id
		return super(InternalMoveRequestLine,self).create(cr,uid,vals,context=context)
	def on_change_product(self,cr,uid,ids,product_id):
		res={}
		product = self.pool.get('product.product').browse(cr,uid,product_id,{})
		res = {'value':{'uom_id':product.uom_id.id}}
		return res

	# FOR STATE FIELD
	def _getParentState(self,cr,uid,ids,field_name,args,context={}):
		res = {}
		for data in self.browse(cr,uid,ids,context):
			res[data.id] = data.internal_move_request_id.state
		return res

	def _getStates(self,cr,uid,context={}):
		im_r = self.pool.get('internal.move.request').getStates(cr,uid,context)
		return im_r


	def _getProcessedItem(self,cr,uid,ids,field_name,args,context={}):
		res={}

		query = "SELECT SUM(a.qty) AS total FROM internal_move_line AS a JOIN internal_move as b ON a.internal_move_id = b.id WHERE a.internal_move_request_line_id = %s AND b.state not in ('cancel','draft')"
		for tid in ids:
			cr.execute(query,[tid])
			theRes = cr.fetchone()
			if theRes[0]:
				res[tid] = theRes[0]
			else:
				res[tid] = 0


		return res
	_name='internal.move.request.line'
	_columns={
		'desc':fields.text('Description',required=False),
		'internal_move_request_id':fields.many2one('internal.move.request',string="Move Req",required=True,ondelete="CASCADE"),
		'no':fields.integer('No',required=True),
		'product_id':fields.many2one('product.product',string="Product",required=True),
		'qty':fields.float('Qty',required=True),
		'uom_id':fields.many2one('product.uom',string='UOM',required=True,readonly=True),
		'state':fields.function(_getParentState,store=False,method=True,string="State",type="selection",selection=_getStates),
		'processed_item_qty':fields.function(_getProcessedItem,store=False,method=True,string="Processed Item",type="float"),
	}
	_rec_name="no"
	_defaults={
		'state':'draft'
	}
class StockPickingInternalMove(osv.osv):
	_inherit='stock.picking'
	_columns={
		'internal_move_id':fields.many2one('internal.move',string="Internal Move",required=False,onupdate="CASCADE",ondelete="CASCADE"),
	}

class StockMoveInternalMove(osv.osv):
	_inherit='stock.move'
	_columns={
		'internal_move_line_id':fields.many2one('internal.move.line',string="Internal Move Line",required=False,onupdate="CASCADE",ondelete="CASCADE"),
		'internal_move_line_detail_id':fields.many2one('internal.move.line.detail',string="Internal Move Line Detail",required=False,onupdate="CASCADE",ondelete="CASCADE"),
	}

class InternalMove(osv.osv):

	STATES = [
		('draft','Draft'),
		('confirmed','Confirmed'),
		('checked','Checked'),
		('ready','Ready to Transfer'),
		('transfered','Transfer'),
		('done','Received'),
		('cancel','Cancel'),
	]


	# GET STATE CONSTANT
	def getStates(self,cr,uid,context={}):
		return self.STATES

	def _setBreaker(cr,uid,product):
		# check if has phantom sets
		if product.bom_ids:
			print product.name," HAS BOM"
			
	def checkSet(self,cr,uid,product):
		res = False
		if product.bom_ids:
			bom = product.bom_ids[0]
			
			if bom.type=='phantom':
				res = bom

		return res

	def _loadLines(self,cr,uid,request,context={}):
		
		res = [(0,0,self._im_line_preparation(cr,uid,line,context=context)) for line in request.lines if (line.qty-line.processed_item_qty) > 0]

		return res
	def prepareBomLine(self,cr,uid,bom_line,im_line):
		res = {}
		res = {
			'no':im_line.no,
			'product_id':bom_line.product_id.id,
			'uom_id':bom_line.product_uom.id,
			'qty':(im_line.qty-im_line.processed_item_qty)*bom_line.product_qty,
			'qty_available':bom_line.product_id.qty_available,
			'type':'sets',
			'state':'draft',
		}
		return res
	# to load internal move line detail automatic by detecting product is has set phantom bom
	def _loadLineDetail(self,cr,uid,line):
		mrp = self.checkSet(cr,uid,line.product_id)
		res = []
		if mrp:
			res = [(0,0,self.prepareBomLine(cr,uid,bom_line,line)) for bom_line in mrp.bom_lines]

		return res



	def _im_line_preparation(self,cr,uid,line,context={}):
		# check for sets
		# set = self.checkSet(cr,uid,line.product_id)
		res = {
			'no':line.no,
			'product_id':line.product_id.id,
			'desc':line.desc,
			'uom_id':line.uom_id.id,
			'qty':line.qty-line.processed_item_qty,
			'qty_available':line.product_id.qty_available,
			'internal_move_request_line_id':line.id,
			'detail_ids':self._loadLineDetail(cr,uid,line),
			'state':'draft',
			'source':context['location'],
			'destination':context['destination']

		}
		return res

	def load_request(self, cr, uid, ids, req_id, source=None, context={}):
		
		res = {'value':{}}
		data = self.pool.get('internal.move.request').browse(cr,uid,req_id,context)
		if data:
			if not source:
				context['location']=data.source.id
				context['location_id']=data.source.id
			else:
				context['location']=source
				context['location_id']=source

			context['destination']=data.destination.id #set destination for im line

			res['value'] = {
				'source':source or data.source.id,
				'destination':data.destination.id,'due_date_transfer':data.due_date,
				'lines':self._loadLines(cr,uid,data,context=context),
				'manual_pb_no':data.manual_pb_no,
				'ref_no':data.ref_no,
				'state':'draft',
				'notes':data.notes,
			}
		return res

	def _prepareMoveLine(self,cr,uid,line,vals):
		res = {
			'location_id':vals['source'],
			'location_dest_id':vals['destination'],
			'no':line[2]['no'],
			'product_id':line[2]['product_id'],	
			'product_qty':line[2]['qty'],
			'product_uom':line[2]['uom_id'],
			'origin':"PB No : "+vals['manual_pb_no'],
		}
		return res
	def validateLot(self,line):
		res =True
		if not line.detail_ids:
			raise osv.except_osv(('Error !!!'), ('Please Pick one or more serial for '+line.product_id.name))
			res=False
		else:
			# check total qty
			sumQty = 0
			for detail in line.detail_ids:
				sumQty+=detail.qty
			if line.qty != sumQty:
				# raise osv.except_osv(('Error !!!'), ('Total Qty that your pick in '+line.product_id.name+' is not valid !Please Check Again..!'))
				raise osv.except_osv(('Error !!!'), ('The Qty that Requested in Item is '+str(line.qty)+' '+line.uom_id.name+', but the total in detail is '+str(sumQty)+' '))
				res = False
		return res


	def _update_im_line_stock_move(self,cr,uid,line_ids,stock_move_id,to='line',context={}):
		return self.pool.get('internal.move.'+to).write(cr,uid,line_ids,{'stock_move_id':stock_move_id},context)

	# CHECK LINE PRODUCT IF DEFINED AS SET OR DEFINED AS BATCHES PRODUCT IT WILL BE HAVA ONE OR MORE detail_ids
	def _checkLineForDetail(self,cr,uid,line_data,context={}):
		res = False
		
		if line_data.product_id.bom_ids and line_data.product_id.supply_method=="manufacture":
			# if has bom
			if line_data.detail_ids:
				res = True
			else:
				raise osv.except_osv(_("Error!!!"),_(str(line_data.product_id.name_template+" is defined as SET product, please define the BOM inside the line!")))

		else:
			if line_data.product_id.track_outgoing:
				if line_data.detail_ids:
					res = True
				else:
					raise osv.except_osv(_("Error!!!"),_(str(line_data.product_id.name_template+" defined as a batches product, Please pick 1 or more batch/es!!!")))
		return res
	# Validate Qty
	def _finalyCheckQty(self,cr,uid,data,context={}):
		res = True
		for line in data.lines:
			if line.detail_ids:
				# validate available detail
				for detail in line.detail_ids:
					if detail.stock_prod_lot_id:
						# if has batch number defined
						# check available by batch number
						if detail.qty > detail.stock_prod_lot_id.stock_available:
							res = False
							raise osv.except_osv(_("Error !!!"),_("Available Stock For "+str(detail.product_id.name_template)+" on "+str(detail.stock_prod_lot_id.name)+" is "+str(detail.stock_prod_lot_id.stock_available)+" "+str(detail.product_id.uom_id.name)+". Requested Item is "+str(detail.qty)+" "+str(detail.uom_id.name)+"!"))
					else:
						# else set not batches
						if detail.qty > detail.product_id.qty_available:
							res = False
							raise osv.except_osv(_("Error !!!"),_("Available Stock For "+str(detail.product_id.name_template)+" is "+str(detail.product_id.qty_available)+" "+str(detail.product_id.uom_id.name)+". Requested Item is "+str(detail.qty)+" "+str(detail.uom_id.name)+"!"))
			else:
				# if not has detail
				if line.qty>line.product_id.qty_available:
					res = False
					raise osv.except_osv(_("Error !!!"),_("Available Stock For "+str(line.product_id.name_template)+" is "+str(line.product_id.qty_available)+" "+line.product_id.uom_id.name+". Requested Item is "+str(line.qty)+" "+str(line.uom_id.name)+"!"))

		return res


	def checkedInternalMove(self,cr,uid,ids,context={}):
		res = True
		self.write(cr,uid,ids,{'state':'checked'},context)
		return True
	def confirmInternalMove(self,cr,uid,ids,context={}):
		res = True
		valid = True
		# loop each ids
		for pre_data in self.browse(cr,uid,ids,context):
			context['location'] = pre_data.source.id
			context['location_id'] = pre_data.source.id

			data = self.browse(cr,uid,pre_data.id, context=context)
			getPrefixStorage = self._get_prefix_storage_code(cr,uid,data.id,context)
			if data.source == data.destination:
				res = False
				raise osv.except_osv(_('Error !'),_('Source and Destination Location is Not Valid..!Please Check!'))
			# prepare for new picking
			prepare_picking = {
				'name':self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.inernal.move.seq'),
				'origin':data.manual_pb_no+", "+data.internal_move_request_id.name,
				'state':'draft',
				'internal_move_id':data.id
			}
			picking_id = self.pool.get('stock.picking').create(cr,uid,prepare_picking,context)

			moves_for_line = []
			line_to_delete = []
			# loop each lines
			for line in data.lines:
				move_line = self._prepare_move(data,line,picking_id)
				move_line_id = self.pool.get('stock.move').create(cr,uid,move_line,context)
				self._update_im_line_stock_move(cr,uid,line.id,move_line_id,'line',context)

				self._checkLineForDetail(cr,uid,line,context)
				# self._checkQty(cr,uid,line,context)
				# EACH DETAILS
				if line.detail_ids:
					for detail in line.detail_ids:
						move_detail = self._prepare_move(data,detail,picking_id)
						if detail.type =='sets':
							if detail.product_id.track_outgoing:
								if not detail.stock_prod_lot_id:
									res = False
									raise osv.except_osv(('Error!!!'),_('Batch Must picked in '+str(detail.product_id.name)+'!'))
								else:
									move_detail = self._prepare_move(data,detail,picking_id,detail.stock_prod_lot_id.id,move_line_id)
									res = True
							else:
								move_detail = self._prepare_move(data,detail,picking_id,detail.stock_prod_lot_id.id,move_line_id)
								res= True
							self._write_autovalidate(cr,uid,move_line_id,{})
						elif detail.type=='batch':
							move_line = False
							valid = self.validateLot(line)
							res = valid
							if valid:
								# self.pool.get('stock.move').unlink(cr,uid,move_line_id)
								move_detail = self._prepare_move(data,detail,picking_id,detail.stock_prod_lot_id.id,move_line_id)
								# line_to_delete = [move_line_id]
								line_to_delete.append(move_line_id)
						if valid:
							move_detail_id = self.pool.get('stock.move').create(cr,uid,move_detail,{})
							self._update_im_line_stock_move(cr,uid,detail.id,move_detail_id,'line.detail',context)
			if res:
				self._finalyCheckQty(cr,uid,data, context=context)
				updateIm = {}
				if not data.name:
					im_no = getPrefixStorage+self.pool.get('ir.sequence').get(cr, uid, 'internal.move')
					updateIm = {'name':im_no,'state':'confirmed','picking_id':picking_id}
				else:
					updateIm = {'state':'confirmed','picking_id':picking_id}
				data.write(updateIm)
				data.internal_move_request_id.write({'state':'onprocess'})
			if len(line_to_delete):
				self.pool.get('stock.move').unlink(cr,uid,line_to_delete)
		# raise osv.except_osv(('Error !!!'), ('The Qty that Requested in Item is '))
		wf_service = netsvc.LocalService("workflow")
		wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
		return res

	def setAsReady(self,cr,uid,ids,context={}):
		res = {}
		pick = self.pool.get('stock.picking')

		for pre_data in self.browse(cr,uid,ids,context):
			context['location'] = pre_data.source.id
			context['location_id'] = pre_data.source.id

			tid = self.browse(cr, uid, pre_data.id, context=context)
			if self._finalyCheckQty(cr, uid, tid, context=context):
				pick.action_assign(cr, uid,  [tid.picking_id.id])
				tid.write({'state':'ready', 'date_prepared':time.strftime('%Y-%m-%d'), 'packing_notes':context['packing_notes']})
		return res



	def transferMove(self,cr,uid,ids,context={}):
		res = False
		searchLoc = self.pool.get('stock.location').search(cr,uid,[('code','=','TRS')])
		trsLoc=None
		if searchLoc:
			trsLoc = searchLoc[0]
		else:
			raise osv.except_osv(_('ERROR!!!'),_("Please Define Transition with \"TRS\" code and type is Transit"))

		for pre_data in self.browse(cr,uid,ids,context=context):
			context['location'] = pre_data.source.id
			context['location_id'] = pre_data.source.id
			data = self.browse(cr, uid, pre_data.id, context=context)

			if self._finalyCheckQty(cr, uid, data, context=context):
				for move in data.picking_id.move_lines:
					move.write({'location_dest_id':trsLoc})

			self.pool.get('stock.picking').force_assign(cr, uid, [data.picking_id.id])
			wf_service = netsvc.LocalService("workflow")
			wf_service.trg_validate(uid, 'stock.picking', data.picking_id.id, 'button_done', cr)
			data.write({'state':'transfered','date_transfered':time.strftime('%Y-%m-%d')})
			res = True
		return res
	
	def _checkRequestProcessed(self,cr,uid,data,context={}):
		res =True

		for reqLine in data.internal_move_request_id.lines:

			if reqLine.processed_item_qty < reqLine.qty:
				res = False

		if res==True:
			# write request to done
			self.pool.get('internal.move.request').write(cr,uid,[data.internal_move_request_id.id],{'state':'done'})
		return res

	def receiveMove(self,cr,uid,ids,context={}):
		res = False
		for data in self.browse(cr,uid,ids,context):
			for move in data.picking_id.move_lines:
				move.write({'location_dest_id':data.destination.id})
			data.picking_id.write({'state':'done'})
			data.write({'state':'done','date_received':time.strftime('%Y-%m-%d')})
			self._checkRequestProcessed(cr,uid,data,context)
			# raise osv.except_osv(_("error"),_("aaaaaaaaaaaaaaaaaaaaaa"))
			res = True
		return res

	def _get_prefix_storage_code(self,cr,uid,ids,context={}):
		res = None
		data = self.browse(cr,uid,ids,context)
		
		if data.source.code and data.destination.code:
			res = data.source.code+"-"+data.destination.code+'/'+time.strftime('%y')+'/'+self.pool.get('internal.move.request').monthToRoman(time.strftime('%m'))+'/'
		else:
			if not data.source.code:
				raise osv.except_osv(_('Error !'),_('Please Define Code For Storage Location : '+data.source.name))
			else:
				raise osv.except_osv(_('Error !'),_('Please Define Code For Storage Location : '+data.destination.name))
		return res

	def setAsDraftInternalMove(self,cr,uid,ids,context={}):
		res = True
		datas = self.browse(cr,uid,ids,context)
		for data in datas:
			data.write({'state':'draft'})
			self.pool.get('stock.picking').unlink(cr,uid,[data.picking_id.id],context)
			for line in data.lines:
				if line.stock_move_id:
					self.pool.get('stock.move').unlink(cr,uid,[line.stock_move_id.id])
			res = True
		return res

	def _write_autovalidate(self,cr,uid,move_id,context={}):
		au = {
			'picking_id':None,
			'auto_validate':"False",
		}
		
		return self.pool.get('stock.move').write(cr,uid,move_id,au,context)

	def _prepare_move(self,data,detail,picking_id=False,prodlot_id=None,move_dest_id=None):
		
		move_detail = {			
			'location_id':data.source.id,
			'location_dest_id':data.destination.id,
			'no':detail.no,
			'product_id':detail.product_id.id,
			'product_qty':detail.qty,
			'product_uom':detail.uom_id.id,
			'origin':"PB No : "+data.manual_pb_no,
			'name':detail.product_id.name_template,
			'desc':detail.desc,
			'state':'draft',
		}
		if detail.desc:
			move_detail['name'] += ". "+detail.desc
		if picking_id:
			move_detail['picking_id']=picking_id
		if prodlot_id:
			move_detail['prodlot_id'] = prodlot_id
		if move_dest_id:
			move_detail['move_dest_id'] = move_dest_id

		try:
			if detail.internal_move_line_id:
				move_detail['internal_move_line_id'] = detail.internal_move_line_id.id
				move_detail['internal_move_line_detail_id'] = detail.id
		except Exception, e:
			move_detail['internal_move_line_id'] = detail.id
		return move_detail
			

	def validateTotalDetail(self,line):
		res = True
		sums = 0
		for detail in line.detail_ids:
			sums+=detail.qty
		if line.qty!=sums:
			res = False
			# raise osv.except_osv(('Error !!!'), ('The Qty that Requested in Item is '+line.qty+' '+line.uom_id.name+', but the total in detail is '+sums+' '))
			raise osv.except_osv(('Error !!!'),_('The Qty is not Valid'))
		return res


	_name='internal.move'
	_description = "Internal Move"
	_inherit = ['mail.thread']
	_columns={
		'name':fields.char('I.M No.'),
		'internal_move_request_id':fields.many2one('internal.move.request',string='Request No',required=True,domain=[('state','in',['confirmed','onprocess'])]),
		'return_ref_id':fields.many2one('internal.move', string="Return Ref"),
		'due_date_transfer':fields.date('Transfer Due Date'),
		'due_date_preparation':fields.date('Preparation Due Date'),
		'date_prepared':fields.date('Prepared Date'),
		'date_transfered':fields.date('Transfered Date',required=False),
		'date_received':fields.date('Received Date',required=False),
		'source':fields.many2one('stock.location',required=True,string="Source Location"),
		'destination':fields.many2one('stock.location',required=True,string="Destination Location"),
		'state':fields.selection(STATES,string="State"),
		'picking_id':fields.many2one('stock.picking',required=False,string="Picking",onupdate='CASCADE',ondelete="SET NULL"),

		'lines':fields.one2many('internal.move.line','internal_move_id',string="Lines"),
		'manual_pb_no':fields.char('PB No',required=False),
		'ref_no':fields.char('Ref No',required=False),
		'notes':fields.text('Notes',required=False),
		'packing_notes':fields.text('Packing Notes',required=False),
		'print_delivery_count':fields.integer('Print Delivery Count',required=False),
		# 'internal_move_line_detail_ids':fields.one2many()
	}

	_defaults={
		'state':"draft",
		'print_delivery_count':0
	}

	_track = {
		
		'source':{},
		'destination':{},
		'due_date_transfer':{},
		'due_date_preparation':{},
		'note':{},
		'state':{
			'sbm_inherit.im_confirmed': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'confirmed',
			'sbm_inherit.im_checked': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'checked',
			'sbm_inherit.im_ready': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'ready',
			'sbm_inherit.im_transfered': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'transfered',
			'sbm_inherit.im_received': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'received',
			'sbm_inherit.im_canceled': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'canceled',
			'sbm_inherit.im_draft': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'draft',
		},
	}

	def printInternalMovePreparation(self,cr,uid,ids,context={}):
		searchConf = self.pool.get('ir.config_parameter').search(cr, uid, [('key', '=', 'base.print')], context=context)
		browseConf = self.pool.get('ir.config_parameter').browse(cr,uid,searchConf,context=context)[0]
		urlTo = str(browseConf.value)+"moves/print-internal-move-preparation&id="+str(ids[0])+"&uid="+str(uid)

		val = self.browse(cr, uid, ids, context={})[0]

		# Menambahkan Log Informasi User yang print document
		im_object 	= self.pool.get('internal.move')
		user_obj 	= self.pool.get('res.users')
		user_value 	= user_obj.browse(cr, uid, uid)
		msg = _("<em>%s</em>, has Print Delivery. ( %s )" ) % (user_value.login, (datetime.now() + timedelta(hours=7)).strftime("%d-%m-%Y %H:%M:%S"))

		im_object.message_post(cr, uid, [val.id], body=msg, context=context)

		return {
			'type'	: 'ir.actions.client',
			'target': 'new',
			'tag'	: 'print.out',
			'params': {
				# 'id'	: ids[0],
				'redir'	: urlTo
			},
		}

	def printInternalMoveNotes(self,cr,uid,ids,context={}):
		
		searchConf = self.pool.get('ir.config_parameter').search(cr, uid, [('key', '=', 'base.print')], context=context)
		browseConf = self.pool.get('ir.config_parameter').browse(cr,uid,searchConf,context=context)[0]
		urlTo = str(browseConf.value)+"moves/print-internal-move&id="+str(ids[0])+"&uid="+str(uid)

		val = self.browse(cr, uid, ids, context={})[0]

		# Update Count dari print delivery
		print_delivery_count = val.print_delivery_count
		print_delivery_count += 1

		self.write(cr,uid,ids,{'print_delivery_count':print_delivery_count},context=context)

		# Menambahkan Log Informasi User yang print document
		im_object = self.pool.get('internal.move')
		user_obj = self.pool.get('res.users')
		user_value = user_obj.browse(cr, uid, uid)
		msg = _("<em>%s</em>, has Print Delivery.( %s )") % (user_value.login, (datetime.now() + timedelta(hours=7)).strftime("%d-%m-%Y %H:%M:%S"))

		im_object.message_post(cr, uid, [val.id], body=msg, context=context)

		return {
			'type'	: 'ir.actions.client',
			'target': 'new',
			'tag'	: 'print.out',
			'params': {
				# 'id'	: ids[0],
				'redir'	: urlTo
			},
		}

	def action_cancel(self,cr,uid,ids,context={}):
		stock_picking_object = self.pool.get('stock.picking')
		stock_move_object = self.pool.get('stock.move')
		val = self.browse(cr, uid, ids, context={})[0]
		
		get_stock_move_id = self.pool.get('stock.move').search(cr,uid,[('picking_id', '=' , val.picking_id.id)])

		# Update state cancel pada stock move
		for i in get_stock_move_id:
			stock_move_object.write(cr,uid,i,{'state':'cancel'})
		
		# Update state cancel pada stock picking
		stock_picking_object.write(cr,uid,val.picking_id.id,{'state':'cancel'})
		
		# Update state cancel pada internal move
		self.write(cr,uid,ids,{'state':'cancel'},context=context)

		return True

	def action_cancel_to_draft(self,cr,uid,ids,context=None):
		# Update state draft pada internal move
		self.write(cr,uid,ids,{'state':'draft', 'picking_id':None},context=context)

		return True

	def action_reload_line(self,cr,uid,ids,context={}):

		val = self.browse(cr, uid, ids, context={})[0]

		data = val.internal_move_request_id
		
		context['location'] = val.source.id
		context['location_id'] = val.source.id

		context['destination'] = val.destination.id
		context['destination_id'] = val.destination.id

		will_load = self._loadLines(cr,uid,data,context=context) #ini yang belum di load dari mr

		# ambil lines current
		current_lines = val.lines

		# harus di dapat internal_move_request_line_id yang akan di append ke internal_move_line
		mr_lines = data.lines

		for mr_line in mr_lines:
			# loop each mr_lines
			qty = mr_line.qty - mr_line.processed_item_qty
			
			in_current_lines = self.pool.get('internal.move.line').search(cr, uid, [('internal_move_request_line_id','=',mr_line.id), ('internal_move_id','=',val.id)])

			if in_current_lines:
				# jika found di current_lines
				current_processed = 0.0
				for found_line in self.pool.get('internal.move.line').browse(cr, uid, in_current_lines, context=context):
					if val.state in ["confirmed", "checked","ready","transfered","done"]:
						current_processed += found_line.qty
						
				qty = qty+current_processed

			if qty>0:
				if len(will_load)==0:
					will_load.append((0,0,{
						'no':mr_line.no,
						'product_id':mr_line.product_id.id,
						'desc':mr_line.desc,
						'uom_id':mr_line.uom_id.id,
						'qty':qty,
						'qty_available':mr_line.product_id.qty_available,
						'internal_move_request_line_id':mr_line.id,
						'detail_ids':self._loadLineDetail(cr,uid,mr_line),
						'state':'draft',
						'source':context['location'],
						'destination':context['destination']
					}));
				else :
					found_in_load  = False
					for w_load in will_load :
						c_wload = len(w_load)
						if mr_line.id == w_load[(c_wload-1)]['internal_move_request_line_id']:
							w_load[(c_wload-1)]['qty'] = qty;
							found_in_load = True
					if not found_in_load:
						will_load.append((0,0,{
							'no':mr_line.no,
							'product_id':mr_line.product_id.id,
							'desc':mr_line.desc,
							'uom_id':mr_line.uom_id.id,
							'qty':qty,
							'qty_available':mr_line.product_id.qty_available,
							'internal_move_request_line_id':mr_line.id,
							'detail_ids':self._loadLineDetail(cr,uid,mr_line),
							'state':'draft',
							'source':context['location'],
							'destination':context['destination']
						}));
						
		lines_ids = self.pool.get('internal.move.line').search(cr, uid, [('internal_move_id','=',val.id)], context=context)
		self.pool.get('internal.move.line').unlink(cr, uid, lines_ids, context=context)

		self.pool.get('internal.move').write(cr,uid,ids,{'lines':will_load},context=context)

		return True			

	def action_create_return(self,cr,uid,ids,context=None):
		if context is None:
			context = {}
		
		dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'sbm_inherit', 'wizard_create_return_internal_move')
		context.update({
			'active_model': self._name,
			'active_ids': ids,
			'active_id': len(ids) and ids[0] or False
		})
		return {
			'view_mode': 'form',
			'view_id': view_id,
			'view_type': 'form',
			'view_name':'wizard_create_return_internal_move',
			'res_model': 'create.return.internal.move',
			'type': 'ir.actions.act_window',
			'target': 'new',
			'context': context,
			'nodestroy': True,
		}

class InternalMoveLine(osv.osv):
	_description = "Internal Move Line"
	def create(self,cr,uid,vals,context={}):
		# stock_move = self.pool.get('stock.move')
		# im = self.pool.get('internal.move')

		# im_data = im.browse(cr,uid,vals['internal_move_id'])[0]
		

		vals['name'] = 'IML-'+time.strftime('%y')+self.pool.get('ir.sequence').get(cr, uid, 'internal.move.line')
		return super(InternalMoveLine,self).create(cr,uid,vals,context=context)
	
	
	def _get_available(self,cr,uid,ids,field_name,arg,context={}):
		res = {}
		for tid in self.browse(cr,uid,ids,context):
			res[tid.id]=tid.product_id.qty_available
		return res



	# FOR STATE FIELD
	def _getParentState(self,cr,uid,ids,field_name,args,context={}):
		res = {}
		for data in self.browse(cr,uid,ids,context):
			res[data.id] = data.internal_move_id.state
		return res
	def _getStates(self,cr,uid,context={}):
		im_r = self.pool.get('internal.move').getStates(cr,uid,context)
		return im_r
	def _getStockState(self,cr,uid,ids,field_name,args,context={}):
		res = {}
		
		for data in self.browse(cr,uid,ids,context):
			res[data.id] = "draft"
			if data.stock_move_id:
				res[data.id] = data.stock_move_id.state
		return res
	_name = 'internal.move.line'
	_columns={
		'name':fields.char('Name'),
		'no':fields.integer('No',required=False),
		'desc':fields.text('Description'),
		'internal_move_id':fields.many2one('internal.move',string='Internal Move No',required=True,ondelete="CASCADE",onupdate="CASCADE"),
		'internal_move_request_line_id':fields.many2one('internal.move.request.line',string="IM Req Line"),
		'return_line_ref_id':fields.many2one('internal.move.line',string="Return Line Ref"),
		'product_id':fields.many2one('product.product',string="Product",required=True),
		'uom_id':fields.many2one('product.uom',string="UOM",required=True),
		'qty':fields.float('Qty',required=True),
		'stock_move_id':fields.many2one('stock.move',string="Move",ondelete="SET NULL",onupdate="CSCADE"),
		'detail_ids':fields.one2many('internal.move.line.detail','internal_move_line_id',string="Details"),

		'qty_available':fields.function(_get_available,string="Available Stock",store=False),

		'state':fields.function(_getParentState,store=False,method=True,string="State",type="selection",selection=_getStates),
		'stock_state':fields.function(_getStockState,store=False,method=True,string="Stock Status",type="selection",selection=[('draft', 'New'),
								   ('cancel', 'Cancelled'),
								   ('waiting', 'Waiting Another Move'),
								   ('confirmed', 'Waiting Availability'),
								   ('assigned', 'Available'),
								   ('done', 'Done'),
								   ]),
		'source':fields.many2one('stock.location',required=False,string="Source Location"),
		'destination':fields.many2one('stock.location',required=False,string="Destination Location"),
	}

	_defaults={
		'state':'draft',
	}

	# GET STATE CONSTANT
	def getStates(self,cr,uid,context={}):
		return self.pool.get('internal.move').STATES


	def loadBomLine(self,cr,uid,bom_line,no,line_qty):
		res = {}
		res = {
			'no':no,
			'product_id':bom_line.product_id.id,
			'uom_id':bom_line.product_uom.id,
			'qty':line_qty*bom_line.product_qty,
			'qty_available':bom_line.product_id.qty_available,
			'type':'sets',
			'state':'draft',

		}
		return res
	def on_change_qty_line(self,cr,uid,ids,product_id,qty,no,context={}):
		res={}
		product = self.pool.get('product.product').browse(cr,uid,product_id,{})
		set = self.pool.get('internal.move').checkSet(cr,uid,product)
		if set:
			res = {
				'value':{
					'detail_ids':[(0,0,self.loadBomLine(cr,uid,bom_line,no,qty)) for bom_line in set.bom_lines]
				}
			}
		return res

	def on_change_source_line(self, cr, uid, ids, source, detail_ids, context={}):
		print "ON Change Source Linesssssssssssss",source, detail_ids
		context['location']=source
		context['location_id']=source
		detail_res = []
		if type(detail_ids)==list:
			
			for detail in detail_ids:
				detail_obj_res = [detail[0],detail[1],{}]

				detail_obj = detail[2]
				item_to_pick = self.pool.get('product.product').browse(cr, uid, detail_obj['product_id'], context=context)
				qty_available = item_to_pick.qty_available
				if detail_obj['type'] == 'batch' and detail_obj['stock_prod_lot_id']:
					item_to_pick = self.pool.get('stock.production.lot').browse(cr, uid, detail_obj['stock_prod_lot_id'],context=context) #result as browse non list
					qty_available = item_to_pick.stock_available

				detail_obj['qty_available'] = qty_available
				detail_obj_res[2] = detail_obj
				detail_res.append(detail_obj_res)
		res = {
			'value':{
				'detail_ids':detail_res
			}
			
		}
		print res, "<RESULLLLLLLLLLLLLLLLLLTTTTTTT"
		return res





class InternalMoveLineDetail(osv.osv):
	_description = "Internal Move Line Detail"
	def validateQty(self,cr,uid,ids,qty,available=0,product_id=None,prod_lot_id=None):
		res = True
		if not product_id:
			res = False
			raise osv.except_osv(('Error!!!'),_('Please Fill Product First !')) 
		else:
			if available < qty:
				res = {
					'value':{
						'qty':0.00,
						'qty_available':available
					},
					'warning':{
						'title':'Qty Not Valid',
						'message':'Qty not Enough!'
					}
				}
				# raise osv.except_osv(('Error!!!'),_('Qty not enough !'))
		return res


	def _default_qty_availability(self,cr,uid,ids,field_name,args,context={}):
		res = {}
		prodlot = self.pool.get('stock.production.lot')
		for tid in self.browse(cr,uid,ids,context):
			res[tid.id]=0
			if tid.stock_prod_lot_id:
				# if has batch
				sn = prodlot.browse(cr,uid,tid.stock_prod_lot_id.id,context)
				res[tid.id]=sn.stock_available
			else:
				# if batch not set
				res[tid.id] = tid.product_id.qty_available


		return res
	def create(self,cr,uid,vals,context={}):
		vals['name'] = 'IMLD-'+time.strftime('%Y')+self.pool.get('ir.sequence').get(cr, uid, 'internal.move.line')
		return super(InternalMoveLineDetail,self).create(cr,uid,vals,context=context)

	# FOR STATE FIELD
	def _getParentState(self,cr,uid,ids,field_name,args,context={}):
		res = {}
		for data in self.browse(cr,uid,ids,context):
			res[data.id] = data.internal_move_line_id.state
		return res
	def _getStates(self,cr,uid,context={}):
		states = self.pool.get('internal.move.line').getStates(cr,uid,context)
		return states

	def _getStockState(self,cr,uid,ids,field_name,args,context={}):
		res = {}
		
		for data in self.browse(cr,uid,ids,context):
			res[data.id] = "draft"
			if data.stock_move_id:
				res[data.id] = data.stock_move_id.state
		return res

	_name = 'internal.move.line.detail'
	_columns = {
		'no':fields.integer('Line No',required=False),
		'name':fields.char('Name',required=False),
		'desc':fields.text('Description',required=False),
		# 'internal_move_id':fields.many2one('internal.move',string="Internal Move",required=True),
		'internal_move_line_id':fields.many2one('internal.move.line',string="Internal Move Line No",ondelete="CASCADE",onupdate="CASCADE"),
		'product_id':fields.many2one('product.product',required=True,string="Product"),
		'uom_id':fields.many2one('product.uom',required=True,string="UOM"),
		'qty':fields.float('Qty',required=True),
		'stock_move_id':fields.many2one('stock.move',string="Move",required=False,ondelete="SET NULL",onupdate="CSCADE"),
		'stock_prod_lot_id':fields.many2one('stock.production.lot',required=False,string="Batch No"),
		'type':fields.selection([('sets','Sets'),('batch','Batch')],string="Type",required=True),

		'qty_available':fields.function(_default_qty_availability,string="Available",store=False),

		'state':fields.function(_getParentState,store=False,method=True,string="State",type="selection",selection=_getStates),
		'stock_state':fields.function(_getStockState,store=False,method=True,string="Stock Status",type="selection",selection=[
			('draft', 'New'),
			('cancel', 'Cancelled'),
			('waiting', 'Waiting Another Move'),
			('confirmed', 'Waiting Availability'),
			('assigned', 'Available'),
			('done', 'Done'),
			]),
	}
	
	_defaults = {
		# 'product_id':_get_default_product,
		# 'type':'batch'
		'state':'draft',
	}


	def on_change_type(self,cr,uid,ids,type,product_id=None):
		res = {}
		if not product_id:
			raise osv.except_osv(('Error !!!'), ('Please Set Product in Line First !'))
		else:
			product = self.pool.get('product.product').browse(cr,uid,product_id,{})
			if not product:
				raise osv.except_osv(('Error !!!'), ('Product not exist, Please Contact Administrator!'))
			else:
				if type == 'batch':
					res = {
						'value':{
							'product_id':product_id,
							'uom_id':product.uom_id.id
						},
						'domain':{
							'stock_prod_lot_id':[('product_id','=',product_id),('stock_available','>',0)]
						}
					}
				else:
					bom_set = []
					if product.bom_ids:
						bom = product.bom_ids[0]
						bom_set = [bom_line.product_id.id for bom_line in bom.bom_lines]
					res = {
						'value':{
							'product_id':False,
							'uom_id':False,
						},
						'domain':{
							# 'stock_prod_lot_id':[('product_id','=','product_id'),('stock_available','>',0)]
							'product_id':[('id','in',bom_set)]
						}
					}
					
		return res
	def on_change_batch(self,cr,uid,ids,batch=None,source=None,context={}):
		res = {}
		context['location']=source
		context['location_id']=source
		if batch:
			data = self.pool.get('stock.production.lot').browse(cr,uid,batch,context=context)

			if data:
				if data.exp_date:
					if data.desc:
						desc = str(data.desc)+'\n Expire On : '+str(data.exp_date)
					else:
						desc = 'Expire On : '+str(data.exp_date)
				else:
					desc = str(data.desc)
				res = {
					'value':{
						# 'qty':0,
						'qty_available':data.stock_available,
						'desc':desc
					}
				}
		return res
	def on_change_product(self,cr,uid,ids,product_id):
		data = self.pool.get('product.product').browse(cr,uid,product_id,{})
		return {
			'value':{
				'uom_id':data.uom_id.id,
				'qty_available':0,
			},
			'domain':{
				'stock_prod_lot_id':[('product_id','=',product_id)]
			}
		}



class SuperNotes(osv.osv):
	_description = "SUPER NOTES"
	_name = 'super.notes'
	_columns = {
		'name':fields.char(required=True,string="Name",size=80),
		'desc':fields.text('Description',required=True),
		'template_note':fields.text('Note Template',required=True),
		'products':fields.many2many('product.product','super_note_product_rel','super_note_id','product_id',string="Super Note Product"),
		'show_in_do_line':fields.boolean('Show In Delivery Order Line ?'),
		'show_in_dn_line':fields.boolean('Show In Delivery Note Line ?'),
	}

class ProductSuperNotes(osv.osv):
	_inherit = 'product.product'
	_name = 'product.product'
	# _table = 'product_product'
	_columns = {
		'super_notes_ids':fields.many2many('super.notes','super_note_product_rel','product_id','super_note_id',string="Note Templates"),
	}


class SalesManTarget(osv.osv):
	_name = 'sales.man.target'
	_columns = {
		'name': fields.char('Code',required=True),
		'user_id':fields.many2one('res.users',string="Sales Man",required=True,ondelete="RESTRICT",onupdate="CASCADE"),
		'year':fields.char('Year',required=True),
		'amount_target':fields.float('Target',required=True),
	}

	def create(self,cr,uid,vals,context={}):

		target_exists = self.pool.get('sales.man.target').search(cr, uid, [('user_id','=',vals['user_id']),('year','=',vals['year'])],context=context)

		name = ""
		
		sales = self.pool.get('res.users').browse(cr,uid,vals['user_id'],{})
		if target_exists:
			raise osv.except_osv(('Warning !!!'), ('Target For Sales Man '+sales.name+' in '+vals['year']+' Already Set!'))
		else:
			
			vals['name'] = sales['initial']+"="+vals['year']
		return super(SalesManTarget,self).create(cr,uid,vals,context=context)

class sale_advance_payment_inv(osv.osv_memory):
	_inherit = "sale.advance.payment.inv"
	_description = "Sales Advance Payment Invoice"

	def create_invoices(self, cr, uid, ids, context=None):
		sale_obj = self.pool.get('sale.order')
		invoice_obj = self.pool.get('account.invoice')
		invoice_line_obj = self.pool.get('account.invoice.line')
		wizard = self.browse(cr, uid, ids[0], context)

		sale_ids = context.get('active_ids', [])

		so = sale_obj.browse(cr, uid, sale_ids)[0]

		cr.execute("SELECT invoice_id FROM sale_order_invoice_rel WHERE order_id = %s", sale_ids)
		invoice = map(lambda x: x[0], cr.fetchall())

		dp_percentage = 0
		amount_total = 0
		
		for x in invoice:
			inv = invoice_obj.browse(cr, uid, x)
			
			if inv.state <> 'cancel':
				dp_percentage += inv.dp_percentage
				amount_total += inv.amount_total

				if inv.state == 'draft':
					raise osv.except_osv(_('Informasi!'),
					_('Has been found to invoice with draft status'))

				if inv.picking_ids:
					raise osv.except_osv(_('Informasi!'),
					_('Invoice has been created from picking Consolidate'))

		if dp_percentage == 100:
			raise osv.except_osv(_('Informasi'),
				_('Invoice Complate'))
		elif dp_percentage == 0 and amount_total >= so.amount_total:
			raise osv.except_osv(_('Informasi'),
				_('Invoice Complete'))
		elif amount_total >= so.amount_total:
			raise osv.except_osv(_('Informasi'),
				_('Invoice Complete'))
		elif dp_percentage + wizard.amount > 100:
			raise osv.except_osv(_('Warning'),
				_('invoice can not be in the process, the percentage is too large'))
		else:
			print '==========ok===='

		res = super(sale_advance_payment_inv,self).create_invoices(cr,uid,ids,context=context)
		return res

	def _check_is_invoice_by_delivery_note_exist(self,cr,uid,ids,sale_obj):
		
		return True

	def _prepare_advance_invoice_vals(self, cr, uid, ids, context=None):

		print '==========&&&&&&&&&&&&&&&&&&&&&&&&&&=============='
		if context is None:
			context = {}
		sale_obj = self.pool.get('sale.order')
		ir_property_obj = self.pool.get('ir.property')
		fiscal_obj = self.pool.get('account.fiscal.position')
		inv_line_obj = self.pool.get('account.invoice.line')
		wizard = self.browse(cr, uid, ids[0], context)
		sale_ids = context.get('active_ids', [])

		result = []
		for sale in sale_obj.browse(cr, uid, sale_ids, context=context):
			self._check_is_invoice_by_delivery_note_exist(cr,uid,ids,sale)
			val = inv_line_obj.product_id_change(cr, uid, [], wizard.product_id.id,
					uom_id=False, partner_id=sale.partner_id.id, fposition_id=sale.fiscal_position.id)
			res = val['value']

			# determine and check income account
			if not wizard.product_id.id :
				prop = ir_property_obj.get(cr, uid,
							'property_account_income_categ', 'product.category', context=context)
				prop_id = prop and prop.id or False
				account_id = fiscal_obj.map_account(cr, uid, sale.fiscal_position or False, prop_id)
				if not account_id:
					raise osv.except_osv(_('Configuration Error!'),
							_('There is no income account defined as global property.'))
				res['account_id'] = account_id
			if not res.get('account_id'):
				raise osv.except_osv(_('Configuration Error!'),
						_('There is no income account defined for this product: "%s" (id:%d).') % \
							(wizard.product_id.name, wizard.product_id.id,))

			# determine invoice amount
			if wizard.amount <= 0.00:
				raise osv.except_osv(_('Incorrect Data'),
					_('The value of Advance Amount must be positive.'))
			if wizard.advance_payment_method == 'percentage':
				if sale.amount_tax>0.0:
					inv_amount = sale.amount_untaxed * wizard.amount / 100
				else:
					inv_amount = sale.amount_total * wizard.amount / 100

				if not res.get('name'):
					res['name'] = _("Advance of %s %%") % (wizard.amount)
			else:
				inv_amount = wizard.amount
				if not res.get('name'):
					#TODO: should find a way to call formatLang() from rml_parse
					symbol = sale.pricelist_id.currency_id.symbol
					if sale.pricelist_id.currency_id.position == 'after':
						res['name'] = _("Advance of %s %s") % (inv_amount, symbol)
					else:
						res['name'] = _("Advance of %s %s") % (symbol, inv_amount)

			# determine taxes
			if res.get('invoice_line_tax_id'):
				res['invoice_line_tax_id'] = [(6, 0, res.get('invoice_line_tax_id'))]
			else:
				res['invoice_line_tax_id'] = False

			# create the invoice
			inv_line_values = {
				'name': res.get('name'),
				'origin': sale.name,
				'account_id': res['account_id'],
				'price_unit': inv_amount,
				'quantity': wizard.qtty or 1.0,
				'discount': False,
				'uos_id': res.get('uos_id', False),
				'product_id': wizard.product_id.id,
				'invoice_line_tax_id': res.get('invoice_line_tax_id'),
				'account_analytic_id': sale.project_id.id or False,
			}
			inv_values = {
				'name': sale.client_order_ref or sale.name,
				'origin': sale.name,
				'type': 'out_invoice',
				'reference': sale.client_order_ref,
				'account_id': sale.partner_id.property_account_receivable.id,
				'partner_id': sale.partner_invoice_id.id,
				'invoice_line': [(0, 0, inv_line_values)],
				'currency_id': sale.pricelist_id.currency_id.id,
				'comment': '',
				'payment_term': sale.payment_term.id,
				'fiscal_position': sale.fiscal_position.id or sale.partner_id.property_account_position.id,
				'group_id':sale.group_id.id,
			}

			if wizard.advance_payment_method == 'percentage':
				inv_values['payment_for'] = 'dp'
				inv_values['dp_percentage'] = wizard.amount

			result.append((sale.id, inv_values))
		return result

class purchase_partial_invoice(osv.osv_memory):
	_inherit = "purchase.partial.invoice"

	def _prepare_advance_invoice_vals(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		purchase_obj = self.pool.get('purchase.order')
		inv_line_obj = self.pool.get('account.invoice.line')
		wizard = self.browse(cr, uid, ids[0], context)
		purchase_ids = context.get('active_ids', [])

		id_product=self.pool.get('product.product').search(cr,uid,[('default_code', '=' ,'PAYADV')])

		if id_product == []:
			raise osv.except_osv(_('Informasi'), _('Please Create Product PAYADV'))

		data_product =self.pool.get('product.product').browse(cr,uid,id_product)[0]

		result = []
		for purchase in purchase_obj.browse(cr, uid, purchase_ids, context=context):
			val = inv_line_obj.product_id_change(cr, uid, [], purchase.order_line[0].product_id.id, uom_id=False, partner_id=purchase.partner_id.id, fposition_id=purchase.fiscal_position.id)
			if val:
				res = val['value']
				set_account_id = res.get('account_id',data_product.property_account_expense.id)
				set_uom_id = res.get('uos_id', False)
			else:
				set_account_id = data_product.property_account_expense.id
				set_uom_id = data_product.uom_id.id

			if wizard.amount <= 0.00:
				raise osv.except_osv(_('Incorrect Data'), _('The value of Advance Amount must be positive.'))
			
			inv_amount = purchase.amount_untaxed * wizard.amount / 100

			# create the invoice
			inv_line_values = {
				'name': data_product.name + ' ' + str(wizard.amount) + '%',
				'origin': purchase.name,
				'account_id': set_account_id,
				'price_unit': inv_amount,
				'quantity': 1.0,
				'uos_id': set_uom_id,
				'product_id': data_product.id,
				'invoice_line_tax_id': False
			}
			
			inv_values = {
				'name': purchase.partner_ref or purchase.name,
				'origin': purchase.name,
				'type': 'in_invoice',
				'account_id': purchase.partner_id.property_account_payable.id,
				'partner_id': purchase.partner_id.id,
				'invoice_line': [(0, 0, inv_line_values)],
				'currency_id': purchase.pricelist_id.currency_id.id,
				'fiscal_position': purchase.fiscal_position.id or purchase.partner_id.property_account_position.id
			}
			result.append((purchase.id, inv_values))

		return result


purchase_partial_invoice()


class account_bank_statement(osv.osv):
	_inherit = "account.bank.statement"
	_columns = {
		'line_ids': fields.one2many('account.bank.statement.line','statement_id', 'Statement lines',states={'confirm':[('readonly', True)]}),
		'po_id': fields.related('line_ids','po_id', type='many2one', relation='purchase.order', string='Purchase Order'),
		'account_id': fields.related('line_ids','account_id', type='many2one', relation='account.account', string='Account Name'),
		'obi_name': fields.related('line_ids','name', type='string', string='OBI Name'),
		'state': fields.selection([
									('draft', 'New'),
									('open','Open'),
									('confirm', 'Closed'),
									('cancel','Cancel')],
								   'Status', required=True, readonly="1",
								   help='When new statement is created the status will be \'Draft\'.\n'
										'And after getting confirmation from the bank it will be in \'Confirmed\' status.'),
	}

	def action_cancel(self, cr, uid, ids, context={}):
		res = self.write(cr,uid,ids,{'state':'cancel'},context=context)
		return res

account_bank_statement()



class create_return_internal_move(osv.osv_memory):

	def default_get(self, cr, uid, fields, context=None):
		if context is None: 
			context = {}

		active_ids = context['active_ids']
		active_model = context.get('active_model')

		res = super(create_return_internal_move, self).default_get(cr, uid, fields, context=context)
		
		linesData = []
		if active_ids:
			move_data =self.pool.get('internal.move').browse(cr,uid,active_ids)[0]
			if context.get('active_model','') == 'internal.move':
				for x in move_data.lines:
					data =self.pool.get('internal.move.line').browse(cr,uid,x.id)

					p = self.pool.get('internal.move.line').search(cr,uid,[('return_line_ref_id', '=' ,data.id)])

					if p:
						qty_available = data.qty
						
						move_line=self.pool.get('internal.move.line').browse(cr,uid,p)

						for x in move_line:
							qty_available = qty_available - x.qty

						if qty_available <> 0:
							linesData += [self._load_so_line(cr, uid, data)]
					else:
						linesData += [self._load_so_line(cr, uid, data)]

			res.update(name=move_data.name)
			res.update(internal_move_id=move_data.id)

			# Dikarnakan Proses Return Maka Source & Destination di sesuaikan
			res.update(source=move_data.destination.id)
			res.update(destination=move_data.source.id)

			res.update(lines=linesData)

		return res

	def _load_so_line(self, cr, uid, line):
		move_line_item = {}
		qty_available = line.qty

		p=self.pool.get('internal.move.line').search(cr,uid,[('return_line_ref_id', '=' ,line.id)])
		if p:
			move_line=self.pool.get('internal.move.line').browse(cr,uid,p)
			for x in move_line:
				qty_available = qty_available - x.qty

		if qty_available <> 0:
			move_line_item = {
				'product_id'			: line.product_id.id,
				'desc'					: line.desc,
				'qty'					: qty_available,
				'uom_id'				: line.uom_id.id,
				'source'				: line.source.id,
				'destination'			: line.destination.id,
				'internal_move_line_id'	: line.id,
			}

		return move_line_item

	def validasi_product_return(self, cr, uid, data, qty, context=None):
		nilai = 0
		p=self.pool.get('internal.move.line').search(cr,uid,[('return_line_ref_id', '=' ,data.id)])

		if p:	
			move_line=self.pool.get('internal.move.line').browse(cr,uid,p)
			for x in move_line:
				nilai += x.qty

			if qty > nilai:
				raise openerp.exceptions.Warning("Prouct Qty " + data.product_id.default_code + " Melebihi Qty")
		else:
			move_line=self.pool.get('internal.move.line').browse(cr,uid,data.id)

			if qty > move_line.qty:
				raise openerp.exceptions.Warning("Prouct Qty " + data.product_id.default_code + " Melebihi Qty Pengiriman")	

		

		return True

	def request_create_return_internal_move(self,cr,uid,ids,context=None):
		val = self.browse(cr, uid, ids)[0]

		obj_im = self.pool.get("internal.move")
		obj_im_line = self.pool.get("internal.move.line")
		lines = []

		for line in val.lines:
			data = obj_im_line.browse(cr, uid, line.internal_move_line_id.id)
			material_line = []
			for x in data.detail_ids:
				material_line.append((0,0,{
						'no':x.no,
						'name':x.name,
						'desc':x.desc,
						'internal_move_line_id':line.id,
						'product_id':x.product_id.id,
						'uom_id':x.uom_id.id,
						'qty':line.qty,
						'stock_move_id':x.stock_move_id.id,
						'stock_prod_lot_id':x.stock_prod_lot_id.id,
						'type':x.type,
					}))

			validasi = self.validasi_product_return(cr, uid, data, line.qty, context=None)

			if validasi == True:
				lines.append((0,0,{
						'internal_move_request_line_id':data.internal_move_request_line_id.id,
						'return_line_ref_id':data.id,
						'name':data.name,
						'no':data.no,
						'desc':data.desc,
						'product_id':data.product_id.id,
						'uom_id':data.uom_id.id,
						'qty':line.qty,
						'source':val.source.id,
						'destination':val.destination.id,
						'detail_ids':material_line,
					}))

		
		im_id = obj_im.create(cr, uid, {
										'name':'',
										'internal_move_request_id':val.internal_move_id.internal_move_request_id.id,
										'return_ref_id':val.internal_move_id.id,
										'source':val.source.id,
										'destination':val.destination.id,
										'manual_pb_no':val.internal_move_id.manual_pb_no,
										'ref_no':val.internal_move_id.ref_no,
										'lines':lines,
										'state':'draft'
									   })

		pool_data=self.pool.get("ir.model.data")
		action_model,action_id = pool_data.get_object_reference(cr, uid, 'sbm_inherit', "internal_move_form")     
		action_pool = self.pool.get(action_model)
		res_id = action_model and action_id or False
		action = action_pool.read(cr, uid, action_id, context=context)
		action['name'] = 'internal.move.form'
		action['view_type'] = 'form'
		action['view_mode'] = 'form'
		action['view_id'] = [res_id]
		action['res_model'] = 'internal.move'
		action['type'] = 'ir.actions.act_window'
		action['target'] = 'current'
		action['res_id'] = im_id
		return action

	_name = "create.return.internal.move"
	_description = "Create Return Internal Move"
	_columns = {
		'name':fields.char(string='I.M No.'),
		'internal_move_id':fields.many2one('internal.move',required=True,string="Internal Move ID"),
		'source':fields.many2one('stock.location',required=True,string="Source Location"),
		'destination':fields.many2one('stock.location',required=True,string="Destination Location"),
		'lines':fields.one2many('create.return.internal.move.line','lines_id',string="Lines"),
	}

create_return_internal_move()


class create_return_internal_move_line(osv.osv_memory):
	_name="create.return.internal.move.line"
	_description="Create Return Internal Move Line"
	_columns={
		'lines_id':fields.many2one('create.return.internal.move',string="Wizard",required=True,ondelete='CASCADE',onupdate='CASCADE'),
		'name':fields.char('Name'),
		'product_id':fields.many2one('product.product',string="Product",required=True),
		'desc':fields.text('Description'),
		'qty':fields.float('Qty',required=True),
		'uom_id':fields.many2one('product.uom',string="UOM",required=True),
		'source':fields.many2one('stock.location',required=False,string="Source Location"),
		'destination':fields.many2one('stock.location',required=False,string="Destination Location"),
		'internal_move_line_id':fields.many2one('internal.move.line',string="Internal Move Line"),
	}

	_rec_name = 'lines_id'

create_return_internal_move_line()
