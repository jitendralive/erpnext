# ERPNext - web based ERP (http://erpnext.com)
# Copyright (C) 2012 Web Notes Technologies Pvt Ltd
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals
import webnotes
from webnotes.utils import flt
from webnotes import msgprint, _
from webnotes.model.controller import DocListController

class AccountController(DocListController):
	def __init__(self, dt=None, dn=None):
		super(AccountController, self).__init__(dt, dn)
		self.nsm_parent_field = 'parent_account'

	def autoname(self):
		abbr = webnotes.conn.get_value('Company', self.doc.company, 'abbr')
		self.doc.name = self.doc.account_name.strip() + ' - ' + abbr
			
	def validate(self): 
		self.validate_rate_for_tax()
		self.validate_parent()
		self.validate_duplicate_account()
		self.validate_root_details()
		self.validate_mandatory()

	def validate_rate_for_tax(self):
		if self.doc.account_type == 'Tax' and not self.doc.tax_rate:
			msgprint(_("Please Enter Rate"), raise_exception=webnotes.MandatoryError)

	def validate_parent(self):
		"""
			Fetch Parent Details and validation for account not to be created under ledger
		"""
		if self.doc.parent_account:
			if self.doc.parent_account == self.doc.name:
				msgprint(_("You can not assign itself as parent account")
					, raise_exception=webnotes.CircularLinkError)
			elif not self.doc.is_pl_account or not self.doc.debit_or_credit:
				par = webnotes.conn.get_value("Account", \
					self.doc.parent_account, ["is_pl_account", "debit_or_credit"])
				self.doc.is_pl_account = par[0]
				self.doc.debit_or_credit = par[1]
		elif self.doc.account_name not in ['Income','Source of Funds (Liabilities)',\
		 	'Expenses','Application of Funds (Assets)']:
			msgprint(_("Parent Account is mandatory"), raise_exception=webnotes.MandatoryError)
	
	def validate_duplicate_account(self):
		"""Account name must be unique"""
		if (self.doc.__islocal or not self.doc.name) \
				and webnotes.conn.exists("Account", {"account_name": self.doc.account_name, \
				"company": self.doc.company}):
			msgprint(_("Account Name already exists, please rename"), raise_exception=webnotes.NameError)
				
	def validate_root_details(self):
		#does not exists parent
		if self.doc.account_name in ['Income','Source of Funds (Liabilities)', \
				'Expenses', 'Application of Funds (Assets)'] and self.doc.parent_account:
			msgprint(_("You can not assign parent for root account"), 
				raise_exception=webnotes.ValidationError)

		# Debit / Credit
		if self.doc.account_name in ['Income','Source of Funds (Liabilities)']:
			self.doc.debit_or_credit = 'Credit'
		elif self.doc.account_name in ['Expenses','Application of Funds (Assets)']:
			self.doc.debit_or_credit = 'Debit'
				
		# Is PL Account 
		if self.doc.account_name in ['Income','Expenses']:
			self.doc.is_pl_account = 'Yes'
		elif self.doc.account_name in ['Source of Funds (Liabilities)','Application of Funds (Assets)']:
			self.doc.is_pl_account = 'No'

	def validate_mandatory(self):
		if not self.doc.debit_or_credit or not self.doc.is_pl_account:
			msgprint(_("'Debit or Credit' and 'Is PL Account' field is mandatory"), 	
				raise_exception=webnotes.MandatoryError)

	def convert_group_to_ledger(self):
		# if child exists
		if webnotes.conn.exists("Account", {"parent_account": self.doc.name}):
			msgprint(_("Account: %s has existing child. You can not convert \
				this account to ledger.	To proceed, move those children under \
				another parent and try again," % self.doc.name), 
				raise_exception=webnotes.ValidationError)
		else:
			webnotes.conn.set(self.doc, 'group_or_ledger', 'Ledger')
			return 1
			
	def convert_ledger_to_group(self):
		if self.check_gle_exists():
			msgprint(_("Account with existing transaction can not be converted to group."), 
				raise_exception=webnotes.ValidationError)
		elif self.doc.account_type:
			msgprint(_("Cannot convert to Group because Account Type is selected."), 
				raise_exception=webnotes.ValidationError)
		else:
			webnotes.conn.set(self.doc, 'group_or_ledger', 'Group')
			return 1

	def check_gle_exists(self):
		return webnotes.conn.exists("GL Entry", {"account": self.doc.name})

	def on_update(self):
		self.update_nsm_model()

	def update_nsm_model(self):
		import webnotes
		import webnotes.utils.nestedset
		webnotes.utils.nestedset.update_nsm(self)
					
	def on_trash(self):
		self.validate_before_trash()
		# rebuild tree
		from webnotes.utils.nestedset import update_remove_node
		update_remove_node('Account', self.doc.name)

	def validate_before_trash(self):
		"""Account with with existing gl entries cannot be inactive"""
		if not self.doc.parent_account:
			msgprint(_("Root Account can not be deleted"), 
				raise_exception=webnotes.ValidationError)
		if self.check_gle_exists():
			msgprint(_("Account with existing transaction \
				(Sales Invoice / Purchase Invoice / Journal Voucher) can not be trashed"), 
				raise_exception=webnotes.ValidationError)
		if webnotes.conn.exists("Account", {'parent_account': self.doc.name}):
			msgprint(_("Child account exists for this account. You can not trash this account."), 
				raise_exception=webnotes.ValidationError)
	
	def on_rename(self,newdn,olddn):
		new_name = newdn.split(" - ")
		company_abbr = webnotes.conn.get_value("Company", self.doc.company, "abbr")
		
		if new_name[-1].lower() != company_abbr.lower():
			msgprint(_("Please add company abbreviation: <b>%s</b> in \
				new account name" % company_abbr), raise_exception=webnotes.NameError)
		else:
			new_acc_name = " - ".join(new_name[:-1])
			webnotes.conn.set_value("Account", olddn, "account_name", new_acc_name)
