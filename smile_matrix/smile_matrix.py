# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Smile. All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import datetime
import netsvc

try:
    from mako.template import Template as MakoTemplate
except ImportError:
    netsvc.Logger().notifyChannel(_("Label"), netsvc.LOG_ERROR, _("Mako templates not installed"))

from osv import osv, fields



def year_month_tuples(year, month, max_year, max_month):
    # inspired by http://stackoverflow.com/questions/6576187/get-year-month-for-the-last-x-months
    _year, _month, _max_year, _max_month = year, month, max_year, max_month
    if max_year < year or (year==max_year and max_month < month):
        raise StopIteration
    while True:
        yield (_year, _month) # +1 to reflect 1-indexing
        _month += 1 # next time we want the next month
        if (_year==_max_year and _month>_max_month):
            raise StopIteration
        if _month == 13:
            _month = 1
            _year += 1



class smile_matrix(osv.osv_memory):
    _name = 'smile.matrix'

    _columns = {
        'name': fields.char("Name", size=32),
        }

    def _get_project(self, cr, uid, context):
        project_id = context and context.get('project_id',False)
        if project_id:
            return self.pool.get('smile.project').browse(cr, uid, project_id, context)
        return False

    def date_to_str(self, date):
        return date.strftime('%Y%m%d')

    def get_date_range_as_str(self, project):
        return [self.date_to_str(d) for d in self.pool.get('smile.project').get_date_range(project)]

    mako_template = """
        <%
            import datetime
        %>
        <form string="Test">
            <html>
                <style type="text/css">
                    table#smile_matrix {
                        border-spacing: .1em;
                    }
                    table#smile_matrix input {
                        width: 2em;
                        border: 0;
                    }
                    table#smile_matrix tbody td,
                    table#smile_matrix th,
                    table#smile_matrix tfoot tr.boolean_line td {
                        border-style: dotted;
                        border-color: #999
                        padding: .2em;
                    }
                    table#smile_matrix tbody td,
                    table#smile_matrix th {
                        border-width: 0 0 1px;
                    }
                    table#smile_matrix tfoot tr.boolean_line td {
                        border-width: 1px 0 0;
                        font-weight: normal;
                    }
                    table#smile_matrix tfoot span,
                    table#smile_matrix tbody span {
                        float: right;
                        text-align: right;
                    }

                    table#smile_matrix .button.increment {
                        display: block;
                        width: 1.5em;
                        text-align: center;
                    }

                    .wrapper.action-buttons {
                        diplay:none;
                    }

                </style>
                <script type="application/javascript">
                    $(document).ready(function(){
                        $("input[kind!='boolean'][name^='cell_']:not(:disabled)").change(function(){
                            name_fragments = $(this).attr("id").split("_");
                            column_index = name_fragments[2];
                            row_index = name_fragments[1];
                            // Select all fields of the columns we clicked in and sum them up
                            var column_total = 0;
                            $("input[kind!='boolean'][name^='cell_'][name$='_" + column_index + "']:not(:disabled)").each(function(){
                                column_total += parseFloat($(this).val());
                            });
                            $("tfoot span.column_total_" + column_index).text(column_total);
                            // Select all fields of the row we clicked in and sum them up
                            var row_total = 0;
                            $("input[kind!='boolean'][name^='cell_" + row_index + "_']:not(:disabled)").each(function(){
                                row_total += parseFloat($(this).val());
                            });
                            $("tbody span.row_total_" + row_index).text(row_total);
                            // Compute the grand-total
                            var grand_total = 0;
                            $("tbody span[class^='row_total_']").each(function(){
                                grand_total += parseFloat($(this).text());
                            });
                            $("#grand_total").text(grand_total);
                        });
                        $("tbody tr:first input[name^='cell_']:not(:disabled)").trigger('change');

                        // Replace all integer fields by a button template, then hide the original field
                        var button_template = $("#button_template");
                        var cells = $("input[kind!='boolean'][name^='cell_']:not(:disabled)");
                        cells.each(function(i, cell){
                            var $cell = $(cell);
                            $cell.after($(button_template).clone().attr('id', 'button_' + $cell.attr("id")).text($cell.val()));
                            $cell.hide();
                        });
                        // Hide the button template
                        $(button_template).hide();

                        // Cycles buttons
                        var cycling_values = ['0', '0.5', '1'];
                        var buttons = $('.button.increment:not(:disabled)');
                        buttons.click(function(){
                            var button_value_tag = $(this).parent().find('input');
                            var button_label_tag = $(this);
                            var current_index = $.inArray(button_value_tag.val(), cycling_values);
                            var new_index = 0;
                            if(!isNaN(current_index)) {
                                new_index = (current_index + 1) % cycling_values.length;
                            };
                            var new_value = cycling_values[new_index];
                            button_label_tag.text(new_value);
                            button_value_tag.val(new_value);
                            button_value_tag.trigger('change');
                        });

                    });
                </script>
                <span id="button_template" class="button increment">
                    Button template
                </span>
                <table id="smile_matrix">
                    <thead>
                        <tr>
                            <th>Line</th>
                            %for date in date_range:
                                <th>${datetime.datetime.strptime(date, '%Y%m%d').strftime('%d/%m')}</th>
                            %endfor
                            <th>Total</th>
                        </tr>
                    </thead>
                    <tfoot>
                        <tr class="total_line">
                            <td>Total</td>
                            %for date in date_range:
                                <td><span class="column_total_${date}"></span></td>
                            %endfor
                            <td><span id="grand_total"></span></td>
                        </tr>
                        %for line in [l for l in lines if not l.hold_quantities]:
                            <tr class="boolean_line">
                                <td>${line.name}</td>
                                %for date in date_range:
                                    <td>
                                        <field name="${'cell_%s_%s' % (line.id, date)}" widget="boolean"/>
                                    </td>
                                %endfor
                                <td></td>
                            </tr>
                        %endfor
                    </tfoot>
                    <tbody>
                        %for line in [l for l in lines if l.hold_quantities]:
                            <tr>
                                <td>${line.name}</td>
                                %for date in date_range:
                                    <td>
                                        <field name="${'cell_%s_%s' % (line.id, date)}"/>
                                    </td>
                                %endfor
                                <td><span class="row_total_${line.id}"></span></td>
                            </tr>
                        %endfor
                    </tbody>
                </table>
                <button string="Validate" name="validate" type="object"/>
            </html>
            <button string="Truc" name="machin" type="object"/>
        </form>
        """

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        project = self._get_project(cr, uid, context)
        if not project:
            return super(smile_matrix, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
        fields = self.fields_get(cr, uid, context=context)
        date_range = self.get_date_range_as_str(project)
        arch = MakoTemplate(self.mako_template).render_unicode(date_range=date_range, lines=project.line_ids, format_exceptions=True)
        return {'fields': fields, 'arch': arch}

    def validate(self, cr, uid, ids, context=None):
        if len(ids) != 1:
            raise osv.except_osv('Error', 'len(ids) !=1')
        # Parse and clean-up data comming from the matrix
        matrix_values = self.read(cr, uid, ids[0])
        for (cell_name, cell_value) in matrix_values.items():
            # Filters out non cell values
            if not cell_name.startswith('cell_'):
                continue
            cell_name_fragments = cell_name.split('_')
            line_id = int(cell_name_fragments[1])
            cell_date = datetime.datetime.strptime(cell_name_fragments[2], '%Y%m%d')
            # Get the line
            line = self.pool.get('smile.project.line').browse(cr, uid, line_id, context)
            # Convert the raw value to the right one depending on the type of the line
            if line.hold_quantities:
                # Quantity conversion
                if type(cell_value) is type(''):
                    cell_value = float(cell_value)
                else:
                    cell_value = None
            else:
                # Boolean conversion
                if cell_value == '1':
                    cell_value = True
                else:
                    cell_value = False
            # Ignore non-modified cells
            if cell_value is None:
                continue
            # Prepare the cell value
            vals = {}
            if line.hold_quantities:
                vals.update({'quantity': cell_value})
            else:
                vals.update({'boolean_value': cell_value})
            # Search for an existing cell at the given date
            cell = self.pool.get('smile.project.line.cell').search(cr, uid, [('date', '=', cell_date), ('line_id', '=', line_id)], context=context, limit=1)
            # Cell doesn't exists, create it
            if not cell:
                vals.update({
                    'date': cell_date,
                    'line_id': line_id,
                    })
                self.pool.get('smile.project.line.cell').create(cr, uid, vals, context)
            # Update cell with our data
            else:
                cell_id = cell[0]
                self.pool.get('smile.project.line.cell').write(cr, uid, cell_id, vals, context)
        return {'type': 'ir.actions.act_window_close'}

    def machin(self, cr, uid, ids, context=None):
        return True

    def create(self, cr, uid, vals, context=None):
        today = datetime.datetime.today()
        for (cell_id, (cell_value, cell_type)) in vals.items():
            field_id = cell_id
            if cell_id not in self._columns:
                cell_date = cell_id.split('_')[2]
                field_props = {
                    'string': cell_date,
                    'type': cell_type,
                    }
                # Make the cell active
                if cell_value is not None:
                    field_props.update({
                        'required': True,
                        'readonly': False,
                        })
                # Disable the cell
                else:
                    field_props.update({
                        'required': False,
                        'readonly': True,
                        })
                field_class = getattr(fields, cell_type)
                self._columns[field_id] = field_class(create_date=today, **field_props)
            elif hasattr(self._columns[field_id], 'create_date'):
                self._columns[field_id].create_date = today
        return super(smile_matrix, self).create(cr, uid, dict([(k, v) for (k, (v, t)) in vals.items()]), context)

    def vaccum(self, cr, uid, force=False):
        super(smile_matrix, self).vaccum(cr, uid, force)
        today = datetime.datetime.today()
        fields_to_clean = []
        for f in self._columns:
            if hasattr(self._columns[f], 'create_date') and (self._columns[f].create_date < today  - datetime.timedelta(days=1)):
                unused = True
                for val in self.datas.values():
                    if f in val:
                        unused=False
                        break
                if unused:
                    fields_to_clean.append(f)
        for f in fields_to_clean:
            del self._columns[f]
        return True

smile_matrix()