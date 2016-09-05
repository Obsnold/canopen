import xml.etree.ElementTree as etree
from canopen import objectdictionary


DATA_TYPES = {
    "INTEGER8": objectdictionary.INTEGER8,
    "INTEGER16": objectdictionary.INTEGER16,
    "INTEGER32": objectdictionary.INTEGER32,
    "UNSIGNED8": objectdictionary.UNSIGNED8,
    "UNSIGNED16": objectdictionary.UNSIGNED16,
    "UNSIGNED32": objectdictionary.UNSIGNED32,
    "REAL32": objectdictionary.REAL32,
    "VISIBLE_STRING": objectdictionary.VIS_STR
}


def import_epf(filename):
    od = objectdictionary.ObjectDictionary()
    tree = etree.parse(filename).getroot()

    # Parse Object Dictionary
    for group_tree in tree.iterfind("Dictionary/Parameters/Group"):
        name = group_tree.get("SymbolName")
        parameters = group_tree.findall("Parameter")
        index = int(parameters[0].get("Index"), 0)

        if len(parameters) == 1:
            # Simple variable
            var = build_variable(parameters[0])
            od.add_object(var)
        elif len(parameters) == 2 and parameters[1].get("ObjectType") == "ARRAY":
            # Array
            arr = objectdictionary.Array(name, index)
            arr.variable = build_variable(parameters[1])
            od.add_object(arr)
        else:
            # Complex record
            record = objectdictionary.Record(name, index)
            for par_tree in parameters:
                var = build_variable(par_tree)
                record.add_member(var)
            od.add_object(record)

    return od


def build_variable(par_tree):
    index = int(par_tree.get("Index"), 0)
    subindex = int(par_tree.get("SubIndex"))
    name = par_tree.get("SymbolName")
    data_type = par_tree.get("DataType")

    par = objectdictionary.Variable(name, index, subindex)
    factor = float(par_tree.get("Factor", 1.0))
    par.factor = int(factor) if factor.is_integer() else factor
    par.unit = par_tree.get("Unit", "")
    par.data_type = DATA_TYPES[data_type]
    try:
        par.min = int(par_tree.get("MinimumValue"))
    except (ValueError, TypeError):
        pass
    try:
        par.max = int(par_tree.get("MaximumValue"))
    except (ValueError, TypeError):
        pass

    # Find value descriptions
    for value_field_def in par_tree.iterfind("ValueFieldDefs/ValueFieldDef"):
        value = int(value_field_def.get("Value"), 0)
        desc = value_field_def.get("Description")
        par.add_value_description(value, desc)

    return par