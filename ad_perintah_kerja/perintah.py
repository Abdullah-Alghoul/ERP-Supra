import time
import netsvc
import decimal_precision as dp
from tools.translate import _
from osv import fields, osv
from datetime import datetime, timedelta


class perintah_kerja(osv.osv):
	_name = "perintah.kerja"
	_columns = {
		'name': fields.char('Work Order', required=True, size=64, readonly=True, states={'draft': [('readonly', False)]}),
		'date' : fields.date('Order Date', required=True, readonly=True, states={'draft': [('readonly', False)]}),
		'type': fields.selection([('other', 'Others'), ('pabrikasi', 'Pabrikasi'), ('man', 'Man Power'), ('service', 'Service')], 'Type', readonly=True, states={'draft': [('readonly', False)]}),
		'sale_id': fields.many2one('sale.order', 'Sale Order', required=False, readonly=True, domain=[('state','in', ('progress','manual'))], states={'draft': [('readonly', False)]}),
		'partner_id': fields.many2one('res.partner', 'Customer', domain=[('customer','=', True)], readonly=True, states={'draft': [('readonly', False)]}),
		'kontrak': fields.char('Contract No', size=64, readonly=True, states={'draft': [('readonly', False)]}),
		'kontrakdate' : fields.date('Contract Date', required=True, readonly=True, states={'draft': [('readonly', False)]}),
		'workshop': fields.char('Working Place', size=64, readonly=True, states={'draft': [('readonly', False)]}),
		'state': fields.selection([('draft', 'Draft'), ('approve', 'Approved'), ('done', 'Done'), ('cancel', 'Cancel')], 'State', readonly=True),
		'perintah_lines': fields.one2many('perintah.kerja.line', 'perintah_id', 'Work Lines', readonly=True, states={'draft': [('readonly', False)]}),
		'material_lines': fields.one2many('raw.material.line', 'perintah_id', 'Material Consumption', readonly=True, states={'draft': [('readonly', False)]}),
		'delivery_date' : fields.date('Delivery Date', required=False, readonly=True, states={'draft': [('readonly', False)]}),
		'write_date': fields.datetime('Date Modified', readonly=True),
		'write_uid':  fields.many2one('res.users', 'Last Modification User', readonly=True),
		'create_date': fields.datetime('Date Created', readonly=True),
		'create_uid':  fields.many2one('res.users', 'Creator', readonly=True),
		'creator' : fields.many2one('res.users', 'Created by'),
		'checker' : fields.many2one('res.users', 'Checked by'),
		'approver' : fields.many2one('res.users', 'Approved by'),
		'note': fields.text('Notes'),
		'terms':fields.text('Terms & Condition'),
		'location_src_id': fields.many2one('stock.location', 'Raw Materials Location', required=True, readonly=True, states={'draft':[('readonly',False)]}),
		'location_dest_id': fields.many2one('stock.location', 'Finished Products Location', required=True, readonly=True, states={'draft':[('readonly',False)]}),
		
	}
	
	_defaults = {
		'name': '/',
		'note': '-',
		'type': 'pabrikasi',
		'state': 'draft',
		'location_src_id': 14,
		'location_dest_id': 14,
		'date': time.strftime('%Y-%m-%d'),
		'kontrakdate': time.strftime('%Y-%m-%d'), 
	}
	 
	_order = "name desc"
	
	def create(self, cr, uid, vals, context=None): 
		# print vals
		if vals['special']==True:
			person = self.pool.get('res.users').browse(cr, uid, uid)
			rom = [0, 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']
			# usa = 'SPC'
			usa = str(self.pool.get('pr').browse(cr, uid, vals['pr_id']).salesman_id.initial)
			val = self.pool.get('ir.sequence').get(cr, uid, 'perintah.kerja').split('/')
			use = str(person.initial)
			vals['creator'] = person.id
			vals['name'] = val[-1]+'A/SBM-ADM/'+usa+'-'+use+'/'+rom[int(val[2])]+'/'+val[1]
			return super(perintah_kerja, self).create(cr, uid, vals, context=context)            
		else:
			person = self.pool.get('res.users').browse(cr, uid, uid)
			rom = [0, 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']
			usa = str(self.pool.get('sale.order').browse(cr, uid, vals['sale_id']).user_id.initial)
			val = self.pool.get('ir.sequence').get(cr, uid, 'perintah.kerja').split('/')
			use = str(person.initial)
			vals['creator'] = person.id
			vals['name'] = val[-1]+'A/SBM-ADM/'+usa+'-'+use+'/'+rom[int(val[2])]+'/'+val[1]
			return super(perintah_kerja, self).create(cr, uid, vals, context=context)    
		
		# oldd
		# person = self.pool.get('res.users').browse(cr, uid, uid)
		# rom = [0, 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']
		# usa = str(self.pool.get('sale.order').browse(cr, uid, vals['sale_id']).user_id.initial)
		# val = self.pool.get('ir.sequence').get(cr, uid, 'perintah.kerja').split('/')
		# use = str(person.initial)
		# vals['creator'] = person.id
		# vals['name'] = val[-1]+'A/SBM-ADM/'+usa+'-'+use+'/'+rom[int(val[2])]+'/'+val[1]
		# return super(perintah_kerja, self).create(cr, uid, vals, context=context)
		# return False

	def sale_change(self, cr, uid, ids, sale):
		if sale:
			res = {}; line = []
			obj_sale = self.pool.get('sale.order').browse(cr, uid, sale)
			for x in obj_sale.order_line:
				line.append({
							 'product_id' : x.product_id.id,
							 'product_qty': x.product_uom_qty,
							 'product_uom': x.product_uom.id,
							 'name': x.name
							 # 'name': '['+str(x.product_id.code)+']' + ' ' + x.product_id.name
							 })
			  
			res['perintah_lines'] = line
			res['kontrak'] = obj_sale.client_order_ref
			res['partner_id'] = obj_sale.partner_id.id
			res['kontrakdate'] = obj_sale.date_order
			res['delivery_date'] = obj_sale.delivery_date
			 
			return  {'value': res}
		return True

	def work_cancel(self, cr, uid, ids, context=None):
		self.write(cr, uid, ids, {'state': 'draft'})
		return True

	def btn_cancel(self, cr, uid, ids, context=None):
		self.write(cr, uid, ids, {'state': 'cancel'})
		return True                             
		 
	def work_confirm(self, cr, uid, ids, context=None):
		val = self.browse(cr, uid, ids)[0]
		if not val.perintah_lines:
			raise osv.except_osv(('Perhatian !'), ('Tabel work line harus diisi !'))
		self.write(cr, uid, ids, {'state': 'approve', 'checker': self.pool.get('res.users').browse(cr, uid, uid).id})
		return True

	def work_validate(self, cr, uid, ids, context=None):
		val = self.browse(cr, uid, ids, context={})[0]
		if val.type == 'pabrikasi' :
			seq_out_mnfct = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.out.manufacture')
			seq_from_mnfct = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.from.manufacture')
			
			if not seq_out_mnfct:
				raise osv.except_osv(_('Error'), _('stock.picking.out.manufacture Sequence not exist.\nPlease contact system administrator'))
			
			if not seq_from_mnfct:
				raise osv.except_osv(_('Error'), _('stock.picking.from.manufacture Sequence not exist.\nPlease contact system administrator.'))
			
			material_id = self.pool.get('stock.picking').create(cr,uid, {
									'name': seq_out_mnfct,
									'origin': val.name,
									'type': 'internal',
									'move_type': 'one',
									'state': 'draft',
									'date': val.date,
									'auto_picking': True,
									'company_id': 1,
								})
			
			goods_id = self.pool.get('stock.picking').create(cr,uid, {
									'name': seq_from_mnfct,
									'origin': val.name,
									'type': 'internal',
									'move_type': 'one',
									'state': 'draft',
									'date': val.date,
									'auto_picking': True,
									'company_id': 1,
								})
			
			for x in val.material_lines:
				self.pool.get('stock.move').create(cr,uid, {
									'name': x.product_id.default_code + x.product_id.name_template,
									'picking_id': material_id,
									'product_id': x.product_id.id,
									'product_qty': x.product_qty,
									'product_uom': x.product_uom.id,
									'date': val.date,
									'location_id': val.location_src_id.id,
									'location_dest_id': 7,
									'state': 'waiting',
									'company_id': 1})
			prodlot = self.pool.get('stock.production.lot')
			for x in val.perintah_lines:
				prodlot_obj_id = False
				if x.product_id.track_production:
					# check if manufacture lot exists
					lot_name_ws = x.product_id.default_code+'-WS'
					get_lot = prodlot.search(cr, uid, [('product_id','=',x.product_id.id), ('name','=',lot_name_ws)])
					if not get_lot:
						# set new serial
						prodlot_obj_id = prodlot.create(
							cr, uid, 
							{
								'name': lot_name_ws, 
								'product_id': x.product_id.id,
								'desc': 'Manufacture Lot',
							}, 
							context=context
						)
					else:
						prodlot_obj_id = get_lot[0]


					# set serial number for manufacture lot
				print prodlot_obj_id,">>>>>>>>>>>>>>"

				self.pool.get('stock.move').create(cr,uid, {
									'name': x.product_id.default_code + x.product_id.name_template,
									'picking_id': goods_id,
									'product_id': x.product_id.id,
									'product_qty': x.product_qty,
									'product_uom': x.product_uom.id,
									'date': val.date,
									'location_id': 7,
									'location_dest_id': val.location_dest_id.id,
									'state': 'waiting',
									'company_id': 1
									,'prodlot_id':prodlot_obj_id or False})
				
			wf_service = netsvc.LocalService("workflow")
			wf_service.trg_validate(uid, 'stock.picking', goods_id, 'button_confirm', cr)
			wf_service.trg_validate(uid, 'stock.picking', material_id, 'button_confirm', cr)

			self.pool.get('stock.picking').force_assign(cr, uid, [goods_id, material_id], context)
							
		self.write(cr, uid, ids, {'state': 'done', 'approver': self.pool.get('res.users').browse(cr, uid, uid).id})
		return True
		   
	def unlink(self, cr, uid, ids, context=None):
		val = self.browse(cr, uid, ids, context={})[0]
		if val.state != 'draft':
			raise osv.except_osv(('Invalid action !'), ('Cannot delete a work order which is in state \'%s\'!') % (val.state,))
		return super(perintah_kerja, self).unlink(cr, uid, ids, context=context)
	 

	def print_perintah(self, cr, uid, ids, context=None):
		data = {}
		val = self.browse(cr, uid, ids)[0]
		data['form'] = {}
		data['ids'] = context.get('active_ids',[])
		data['form']['data'] = self.read(cr, uid, ids)[0]
				
		qty = ''
		product = ''
		for x in val.perintah_lines:
			qty = qty + str(x.product_qty) + ' ' + x.product_uom.name + '\n\n'
			product = product + x.name + '\n\n'
			
		product = product + '\n\n' + val.note 
		
		data['form']['data']['qty'] = qty
		data['form']['data']['product'] = product
		data['form']['data']['creator'] = val.creator.name
		data['form']['data']['checker'] = val.checker.name
		data['form']['data']['approver'] = val.approver.name
		 
		return {
				'type': 'ir.actions.report.xml',
				'report_name': 'perintah.A4',
				'datas': data,
				'nodestroy':True
		}
		
perintah_kerja()


class perintah_kerja_line(osv.osv):
	_name = "perintah.kerja.line"
	_columns = {
		'no': fields.char('No', size=3),
		'name': fields.text('Description'),
		'perintah_id': fields.many2one('perintah.kerja', 'Work Order', required=True, ondelete='cascade'),
		'product_id': fields.many2one('product.product', 'Product'),
		'product_qty': fields.float('Quantity', digits_compute=dp.get_precision('Product UoM')),
		'product_uom': fields.many2one('product.uom', 'UoM'),
	}

	_defaults = {
		'product_uom': 1, 
	}
	 
	 
	def product_change(self, cr, uid, ids, product):
		if product:
			obj_product = self.pool.get('product.product').browse(cr, uid, product)
			res = {'name': '[' + obj_product.code + '] ' + obj_product.name}
			return  {'value': res}
		return True
		
perintah_kerja_line()



class raw_material_line(osv.osv):
	_name = "raw.material.line"
	_columns = {
		'name': fields.char('Description', size=64),
		'perintah_id': fields.many2one('perintah.kerja', 'Work Order', required=True, ondelete='cascade'),
		'product_id': fields.many2one('product.product', 'Product'),
		'product_qty': fields.float('Quantity', digits_compute=dp.get_precision('Product UoM')),
		'product_uom': fields.many2one('product.uom', 'UoM'),
	}

	_defaults = {
		'product_uom': 1, 
	}
	 
	 
	def product_change(self, cr, uid, ids, product):
		if product:
			obj_product = self.pool.get('product.product').browse(cr, uid, product)
			res = {'name': '[' + obj_product.code + '] ' + obj_product.name}
			return  {'value': res}
		return True
		
raw_material_line()
class SaleOrder(osv.osv):
	_inherit = 'sale.order'
	_name = 'sale.order'
	_columns = {
		'pricelist_id': fields.many2one('product.pricelist', 'Currency', required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Pricelist for current sales order."),
		'partner_shipping_id2': fields.many2one('res.partner', 'Delivery Address 2', readonly=False, required=False, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Delivery address for current sales order."),
	}

	def onchange_shop_id(self, cr, uid, ids, shop_id, context=None):
		v = {}
		if shop_id:
			shop = self.pool.get('sale.shop').browse(cr, uid, shop_id, context=context)
			# if shop.project_id.id:
			#     v['project_id'] = shop.project_id.id
			# if shop.pricelist_id.id:
			#     v['pricelist_id'] = shop.pricelist_id.id
		return {'value': v}

	def onchange_partner_id(self, cr, uid, ids, part, context=None):
		if not part:
			return {'value': {'partner_invoice_id': False, 'partner_shipping_id': False,  'payment_term': False, 'fiscal_position': False}}

		part = self.pool.get('res.partner').browse(cr, uid, part, context=context)
		addr = self.pool.get('res.partner').address_get(cr, uid, [part.id], ['delivery', 'invoice', 'contact'])
		pricelist = part.property_product_pricelist and part.property_product_pricelist.id or False
		payment_term = part.property_payment_term and part.property_payment_term.id or False
		fiscal_position = part.property_account_position and part.property_account_position.id or False
		dedicated_salesman = part.user_id and part.user_id.id or uid
		val = {
			'partner_invoice_id': addr['invoice'],
			# 'partner_shipping_id': addr['delivery'],
			'payment_term': payment_term,
			'fiscal_position': fiscal_position,
			'user_id': dedicated_salesman,
		}
		# print '============================',addr
		# if addr is None:
		#     val['partner_shipping_id']= addr['delivery'],
		# if pricelist:
		#     val['pricelist_id'] = pricelist
		return {'value': val}

	def copy_pure_quotation(self,cr,uid,ids,context=None):
		# print "CALLEDDD",ids;
		rec = self.browse(cr,uid,ids,context)[0]
		
		prepareNewSO = {
			'origin':rec.origin,
			'order_policy':rec.order_policy,
			'client_order_ref':rec.client_order_ref,
			'partner_id':rec.partner_id.id,
			'date_order':rec.date_order,
			'note':rec.note,
			'user_id':rec.user_id.id,
			'payment_term':rec.payment_term.id,
			'company_id':rec.company_id.id,
			# 'amount_tax':rec.amount_tax,
			'state':'draft',
			# 'amount_untaxed':rec.amount_untaxed,
			'partner_shipping_id':rec.partner_shipping_id.id,
			'picking_policy':rec.picking_policy,
			'incoterm':rec.incoterm.id,
			'carrier_id':rec.carrier_id.id,
			'worktype':rec.worktype,
			'week':rec.week,
			'attention':rec.attention.id,
			'internal_notes':rec.internal_notes,
			'project_id':rec.project_id.id,
			'pricelist_id':rec.pricelist_id.id,
			'partner_invoice_id':rec.partner_invoice_id.id,
			'group_id':rec.group_id.id

		}
		ListScope1 = []
		ListScope2 = []
		ListTerms = []

		for sSupra in rec.scope_work_supra:
			ListScope1.append(sSupra.id)
		for sCust in rec.scope_work_customer:
			ListScope2.append(sCust.id)
		for sTerm in rec.term_condition:
			ListTerms.append(sTerm.id)

		prepareNewSO['scope_work_supra'] = [(6,0,ListScope1)]
		prepareNewSO['scope_work_customer'] = [(6,0,ListScope2)]
		prepareNewSO['term_condition'] = [(6,0,ListTerms)]

		newOrderId = self.create(cr,uid,prepareNewSO,context)
		print prepareNewSO

		for line in rec.order_line:
			prepareTax = []
			for tax in line.tax_id:
				prepareTax.append(tax.id)
			newLineObj = self.pool.get('sale.order.line')
			newLine = {
				'product_uos_qty':line.product_uos_qty,
				'product_uom':line.product_uom.id,
				'product_uom_qty':line.product_uom_qty,
				# 'discount':line.discount,
				'product_uos':line.product_uos.id,
				'sequence':line.sequence,
				'order_id':newOrderId,
				# 'price_unit':line.price_unit,
				'name':line.name,
				'company_id':line.company_id.id,
				'salesman_id':line.salesman_id.id,
				'state':'draft',
				'product_id':line.product_id.id,
				'order_partner_id':line.order_partner_id.id,
				'th_weight':line.th_weight,
				'type':line.type,
				'address_allotment_id':line.address_allotment_id.id,
				'procurement_id':line.procurement_id.id,
				'delay':line.delay,
				'product_onhand':line.product_onhand,
				'product_future':line.product_future,
				'discount_nominal':line.discount_nominal,
				'tax_id':[(6,0,prepareTax)]
			}
			# print "NEW LINE ",newLine
			newLineObj.create(cr,uid,newLine,context)

		# print "NEW ID    ",newOrderId
		
		
		dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'sale', 'view_order_form')
		return {
			'view_mode': 'form',
			'view_id': view_id,
			'view_type': 'form',
			'view_name':'sale.order.form',
			'res_model': 'sale.order',
			'type': 'ir.actions.act_window',
			'target': 'current',
			'res_id':newOrderId,
			'domain': "[('id','=',"+str(newOrderId)+")]",
		}





#             for x in val.perintah_lines:
#                 if x.product_id.type != 'service':
#                     bom_id = self.pool.get('mrp.bom')._bom_find(cr, uid, x.product_id.id, x.product_uom.id, [])
#                     if not bom_id:
#                         raise osv.except_osv(('Attention !'), ("Cannot find a bill of material for this product."))
#                     self.pool.get('mrp.production').create(cr,uid, {
#                                     'product_id': x.product_id.id,
#                                     'product_qty': x.product_qty,
#                                     'product_uom': x.product_uom.id,
#                                     'workshop': val.workshop,
#                                     'kontrak': val.kontrak,
#                                     'bom_id': bom_id,
#                                     'kontrakdate' : val.kontrakdate,
#                                     'sale_id': val.sale_id.id,
#                                     'perintah_id': val.id})
	
#     def spk_change(self, cr, uid, ids, spk, sale):
#         # ex: 000001A/SBM-ADM/JH-NR/X/13
#         if not sale:
#             raise osv.except_osv(('Attention !'), ('Please select a sales order!'))    
#         kerja = '/'
#         rom = [0, 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']
#         if spk:
#             usa = str(self.pool.get('sale.order').browse(cr, uid, sale).user_id.initial)
#             val = self.pool.get('ir.sequence').get(cr, uid, 'perintah.kerja').split('/')
#             use = str(self.pool.get('res.users').browse(cr, uid, uid).initial)
#             kerja = val[-1]+'A/SBM-ADM/'+usa+'-'+use+'/'+rom[int(val[2])]+'/'+val[1]
#         return  {'value': {'suratkerja': kerja}}
#     
#     def do_change(self, cr, uid, ids, do, sale):
#         # ex: 000001B/SBM-ADM/JH-NR/X/13
#         if not sale:
#             raise osv.except_osv(('Attention !'), ('Please select a sales order!'))
#         kirim = '/'
#         rom = [0, 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']
#         if do:
#             usa = str(self.pool.get('sale.order').browse(cr, uid, sale).user_id.initial)
#             val = self.pool.get('ir.sequence').get(cr, uid, 'pesan.antar').split('/')
#             use = str(self.pool.get('res.users').browse(cr, uid, uid).initial)
#             kirim = val[-1]+'B/SBM-ADM/'+usa+'-'+use+'/'+rom[int(val[2])]+'/'+val[1]
#         return  {'value': {'suratjalan': kirim}}
	
#     def sale_change(self, cr, uid, ids, sale):
#         
#         if sale:
#             res = {}
#             obj_sale = self.pool.get('sale.order').browse(cr, uid, sale)
#             res['prepare_lines'] = [] 
#             res['picking_id'] = False
#             res['partner_id'] = obj_sale.partner_id.id
#             res['kontrak'] = obj_sale.client_order_ref
#              
#             return  {'value': res}
