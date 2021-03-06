wn.query_reports["Gross Profit"] = {
	"filters": [
		{
			"fieldname":"company",
			"label": "Company",
			"fieldtype": "Link",
			"options": "Company",
			"default": wn.defaults.get_user_default("company")
		},
		{
			"fieldname":"from_date",
			"label": "From Date",
			"fieldtype": "Date",
			"default": wn.defaults.get_user_default("year_start_date")
		},
		{
			"fieldname":"to_date",
			"label": "To Date",
			"fieldtype": "Date",
			"default": wn.defaults.get_user_default("year_end_date")
		},
	]
}