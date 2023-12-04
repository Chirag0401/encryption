#!/bin/bash

auth="d6165047b19c9421729ea50b34a389f676338173d50960aa829cd6db7899a07c"
zbx_host="operations.ops.ped.local"
zabbix_url="https://${zbx_host}/api_jsonrpc.php"
existing_dash=$(curl -k -X POST -H "Content-Type: application/json" -d '{"jsonrpc": "2.0", "method": "dashboard.get", "params": { "output": ["name", "dashboardid"]},"id": 2, "auth": "'$auth'"}' "$zabbix_url")
data_file="/tmp/zabbix_dash.json"
Get_Dash_CurrentNRequested_Sharing() { :; }
generate_dark_color() { printf "%02x%02x%02x\n" $((RANDOM%128+127)) $((RANDOM%128+127)) $((RANDOM%128+127)); }

# Retrieve the vm value
vm=$(some_command_to_retrieve_vm_value)  # Replace with actual command to get vm value

# Conditional settings based on vm value
if [[ $vm = *"ppe"* ]] && [[ $vm != *"ppe.wpt"* ]]; then
    ENV="ppe"
    Dash_name="BCS Sales PPE"
    host_group="ppe.bcs-Servers"
    Dash_Sharing_Group=("p-ped-zabbix-nprod-ops" "p-ped-zabbix-nprod-ops-readonly")
    cluster="cluster.msk-ppe"
elif [[ $vm = *"ppe.wpt"* ]]; then
    ENV="ppe"
    Dash_name="WPT PPE"
    host_group="ppe.wpt-Servers"
    Dash_Sharing_Group=("p-ped-zabbix-nprod-admins")
elif [[ $vm = *"sit"* ]]; then
    ENV="sit"
    Dash_name="BCS Sales SIT"
    host_group="sit.bcs-Servers"
    Dash_Sharing_Group=("p-ped-zabbix-nprod-ops" "p-ped-zabbix-nprod-ops-readonly")
    cluster="cluster.msk-sit"
elif [[ $vm = *"ped"* ]]; then
    ENV="ppe"
    Dash_name="PED PPE"
    host_group="ops.ped-servers"
    Dash_Sharing_Group=("p-ped-zabbix-nprod-admins")
elif [[ $vm = *"patch.bcs"* ]]; then
    ENV="patching"
    Dash_name="BCS Sales Patching"
    host_group="patch.bcs-Servers"
    Dash_Sharing_Group=("p-ped-zabbix-nprod-ops" "p-ped-zabbix-nprod-ops-readonly")
elif [[ $vm = *"ppe.shp"* ]]; then
    ENV="ppe"
    Dash_name="Shoppify PPE"
    host_group="ppe.shp-Servers"
    Dash_Sharing_Group=("p-ped-zabbix-nprod-admins")
elif [[ $vm = *"muat.wpt"* ]]; then
    ENV="muat"
    Dash_name="WPT MUAT"
    host_group="muat.wpt-Servers"
    Dash_Sharing_Group=("p-ped-zabbix-prod-ops" "p-ped-zabbix-prod-ops-readonly" "p-ped-zabbix-prod-admins")
elif [[ $vm = *"prod.ops"* ]]; then
    ENV="prod"
    Dash_name="PED PROD"
    host_group="prod.ops-Servers"
    Dash_Sharing_Group=("p-ped-zabbix-prod-ops" "p-ped-zabbix-prod-ops-readonly" "p-ped-zabbix-prod-admins")
elif [[ $vm = *"prod.bcs"* ]]; then
    ENV="prod"
    Dash_name="BCS Sales PROD"
    host_group="prod.bcs-Servers"
    cluster="cluster.msk-prod"
    Dash_Sharing_Group=("p-ped-zabbix-prod-ops" "p-ped-zabbix-prod-ops-readonly" "p-ped-zabbix-prod-admins")
fi

# ... Rest of your existing script follows here ...

case ${existing_dash} in
  *"${Dash_name}"*)
    dash_id=$(echo $existing_dash | grep -o "{[^}]*$Dash_name*" | cut -d ":" -f2 | grep -Eo '[0-9]{1,10}')
    dash_info=$(curl -k -X POST -H "Content-Type: application/json" -d '{"jsonrpc": "2.0", "method": "dashboard.get", "params": { "dashboardids": ["'$dash_id'"], "selectPages": "extend", "output": "extend"},"id": 2, "auth": "'$auth'"}' "$zabbix_url")
    page_id=$(echo $dash_info | grep -o '"dashboard_pageid":"[^"]*' | cut -d ":" -f2 | tr -d '"')
    Get_Dash_CurrentNRequested_Sharing $dash_id "${Dash_Sharing_Group[@]}"
    json_part1='{"jsonrpc": "2.0","method": "dashboard.update","params": {"dashboardid": "'$dash_id'","pages": [{"dashboard_pageid": "'$page_id'","widgets": ['
    ;;
  *)
    Get_Dash_CurrentNRequested_Sharing na "${Dash_Sharing_Group[@]}"
    json_part1='{"jsonrpc":"2.0","method":"dashboard.create","params":{"name":"'$Dash_name'","userid":"1","private":"1","display_period":10,"auto_start":1,"pages":[{"widgets":['
    ;;
esac

echo -n "$json_part1" > $data_file

# Variables for widget placement
top_widget_height=6
top_widget_width=24
graph_widget_height=6
graph_widget_width=12
dashboard_max_width=24  # Dashboard width
dashboard_max_height=62 # Dashboard height
x=0
y=0
i="eu-west-1"
j="wpt"
# netgroup="CORE"
ENV="ppe"
TopHostsCount=100

# Add top_hosts widgets
network_groups=("CORE" "DMZ")
# for metric in "${network_groups[@]}"; do
for netgroup in "${network_groups[@]}"; do
  # Check if adding another widget will exceed the dashboard width
  if (( x + top_widget_width > dashboard_max_width )); then
    # Reset X position to start at the beginning of the next row
    x=0
    # Increment Y position to move to the next row
    y=$((y + top_widget_height))
  fi

  # Check if adding another widget will exceed the dashboard height
  if (( y + top_widget_height > dashboard_max_height)); then 
    echo "Error: Widget placement for 'top_hosts' exceeds dashboard height."
    exit 1
  fi
  # json_top_hosts_widget='{"type":"tophosts","name":"'$ENV'-'$j'","x":"'$x'","y":"'$y'","width":"'$top_widget_width'","height":"'$top_widget_height'","view_mode":"0","fields":[{"type":"0","name":"count","value":"'$TopHostsCount'"},{"type":"1","name":"columns.name.5","value":"Schema Registry"},{"type":"0","name":"columns.data.5","value":"1"},{"type":"1","name":"columns.item.5","value":"Apache: Service ping"},{"type":"1","name":"columns.timeshift.5","value":""},{"type":"0","name":"columns.aggregate_function.5","value":"0"},{"type":"0","name":"columns.display.5","value":"1"},{"type":"0","name":"columns.history.5","value":"1"},{"type":"1","name":"columns.base_color.5","value":""},{"type":"1","name":"columnsthresholds.color.5.0","value":"FF465C"},{"type":"1","name":"columnsthresholds.threshold.5.0","value":"0"},{"type":"1","name":"columnsthresholds.color.5.1","value":"80FF00"},{"type":"1","name":"columnsthresholds.threshold.5.1","value":"1"},{"type":"1","name":"columns.name.4","value":"Agent"},{"type":"0","name":"columns.data.4","value":"1"},{"type":"1","name":"columns.item.4","value":"Zabbix agent availability"},{"type":"1","name":"columns.timeshift.4","value":""},{"type":"0","name":"columns.aggregate_function.4","value":"0"},{"type":"0","name":"columns.display.4","value":"1"},{"type":"0","name":"columns.history.4","value":"1"},{"type":"1","name":"columns.base_color.4","value":""},{"type":"1","name":"columnsthresholds.color.4.0","value":"FF465C"},{"type":"1","name":"columnsthresholds.threshold.4.0","value":"0"},{"type":"1","name":"columnsthresholds.color.4.1","value":"80FF00"},{"type":"1","name":"columnsthresholds.threshold.4.1","value":"1"},{"type":"1","name":"columns.item.2","value":"Memory utilization"},{"type":"1","name":"columns.timeshift.2","value":""},{"type":"0","name":"columns.aggregate_function.2","value":"0"},{"type":"0","name":"columns.display.2","value":"3"},{"type":"0","name":"columns.history.2","value":"1"},{"type":"1","name":"columns.name.3","value":"Disk"},{"type":"0","name":"columns.data.3","value":"1"},{"type":"1","name":"columns.item.3","value":"/: Space utilization"},{"type":"1","name":"columns.timeshift.3","value":""},{"type":"0","name":"columns.aggregate_function.3","value":"0"},{"type":"0","name":"columns.display.3","value":"3"},{"type":"0","name":"columns.history.3","value":"1"},{"type":"1","name":"columns.base_color.3","value":""},{"type":"0","name":"column","value":"1"},{"type":"1","name":"columnsthresholds.color.1.0","value":"FFFF00"},{"type":"1","name":"columnsthresholds.threshold.1.0","value":"50"},{"type":"1","name":"columnsthresholds.color.1.1","value":"FF8000"},{"type":"1","name":"columnsthresholds.threshold.1.1","value":"80"},{"type":"1","name":"columnsthresholds.color.1.2","value":"FF465C"},{"type":"1","name":"columnsthresholds.threshold.1.2","value":"90"},{"type":"1","name":"columnsthresholds.color.2.0","value":"80FF00"},{"type":"1","name":"columnsthresholds.threshold.2.0","value":"50"},{"type":"1","name":"columnsthresholds.color.2.1","value":"FFBF00"},{"type":"1","name":"columnsthresholds.threshold.2.1","value":"80"},{"type":"1","name":"columnsthresholds.color.2.2","value":"FF465C"},{"type":"1","name":"columnsthresholds.threshold.2.2","value":"95"},{"type":"1","name":"tags.tag.0","value":"env"},{"type":"0","name":"tags.operator.0","value":"1"},{"type":"1","name":"tags.value.0","value":"'$ENV'"},{"type":"1","name":"tags.tag.1","value":"region"},{"type":"0","name":"tags.operator.1","value":"1"},{"type":"1","name":"tags.value.1","value":"'$i'"},{"type":"1","name":"tags.tag.2","value":"project"},{"type":"0","name":"tags.operator.2","value":"1"},{"type":"1","name":"tags.value.2","value":"'$j'"},{"type":"1","name":"columns.min.1","value":"0"},{"type":"1","name":"columns.max.1","value":"100"},{"type":"1","name":"columns.base_color.1","value":"80FF00"},{"type":"1","name":"columns.min.2","value":"0"},{"type":"1","name":"columns.max.2","value":"100"},{"type":"1","name":"columns.base_color.2","value":"80FF00"},{"type":"1","name":"columns.min.3","value":"0"},{"type":"1","name":"columns.max.3","value":"100"},{"type":"1","name":"columnsthresholds.color.3.0","value":"FFFF00"},{"type":"1","name":"columnsthresholds.threshold.3.0","value":"80"},{"type":"1","name":"columnsthresholds.color.3.1","value":"FF8000"},{"type":"1","name":"columnsthresholds.threshold.3.1","value":"90"},{"type":"1","name":"columnsthresholds.color.3.2","value":"FF4000"},{"type":"1","name":"columnsthresholds.threshold.3.2","value":"95"},{"type":"1","name":"columns.name.0","value":"Name"},{"type":"0","name":"columns.data.0","value":"2"},{"type":"0","name":"columns.aggregate_function.0","value":"0"},{"type":"1","name":"columns.base_color.0","value":""},{"type":"1","name":"columns.name.1","value":"CPU"},{"type":"0","name":"columns.data.1","value":"1"},{"type":"1","name":"columns.item.1","value":"CPU utilization"},{"type":"1","name":"columns.timeshift.1","value":""},{"type":"0","name":"columns.aggregate_function.1","value":"0"},{"type":"0","name":"columns.display.1","value":"3"},{"type":"0","name":"columns.history.1","value":"1"},{"type":"1","name":"columns.name.2","value":"Memory"},{"type":"0","name":"columns.data.2","value":"1"}]},'
  json_top_hosts_widget='{"type":"tophosts","name":"WPT Hosts-'$netgroup'","x":"'$x'","y":"'$y'","width":'$top_widget_width',"height":"'$top_widget_height'","view_mode":"0","fields":[{"type":"1","name":"tags.tag.0","value":"project"},{"type":"0","name":"tags.operator.0","value":"1"},{"type":"1","name":"tags.value.0","value":"wpt"},{"type":"1","name":"tags.tag.3","value":"NetworkGroup"},{"type":"0","name":"tags.operator.3","value":"1"},{"type":"1","name":"tags.value.3","value":"'$netgroup'"},{"type":"0","name":"tags.operator.1","value":"1"},{"type":"1","name":"columns.name.0","value":"Name"},{"type":"0","name":"columns.data.0","value":"2"},{"type":"0","name":"columns.aggregate_function.0","value":"0"},{"type":"1","name":"columns.base_color.0","value":""},{"type":"1","name":"columns.name.1","value":"CPU"},{"type":"0","name":"columns.data.1","value":"1"},{"type":"1","name":"columns.item.1","value":"CPU utilization"},{"type":"1","name":"columns.timeshift.1","value":""},{"type":"0","name":"columns.aggregate_function.1","value":"0"},{"type":"1","name":"columns.min.1","value":"0"},{"type":"1","name":"columns.max.1","value":"100"},{"type":"0","name":"columns.display.1","value":"3"},{"type":"0","name":"columns.history.1","value":"1"},{"type":"1","name":"columns.base_color.1","value":"80FF00"},{"type":"1","name":"columnsthresholds.color.1.0","value":"FFFF00"},{"type":"1","name":"columnsthresholds.threshold.1.0","value":"50"},{"type":"1","name":"columnsthresholds.color.1.1","value":"FF8000"},{"type":"1","name":"columnsthresholds.threshold.1.1","value":"80"},{"type":"1","name":"columnsthresholds.color.1.2","value":"FF0000"},{"type":"1","name":"columnsthresholds.threshold.1.2","value":"90"},{"type":"1","name":"columns.name.2","value":"Memory"},{"type":"0","name":"columns.data.2","value":"1"},{"type":"1","name":"columns.item.2","value":"Memory utilization"},{"type":"1","name":"columns.timeshift.2","value":""},{"type":"0","name":"columns.aggregate_function.2","value":"0"},{"type":"1","name":"columns.min.2","value":"0"},{"type":"1","name":"columns.max.2","value":"100"},{"type":"0","name":"columns.display.2","value":"2"},{"type":"0","name":"columns.history.2","value":"1"},{"type":"1","name":"columns.base_color.2","value":"00FF00"},{"type":"1","name":"columnsthresholds.color.2.0","value":"00FF00"},{"type":"1","name":"columnsthresholds.threshold.2.0","value":"50"},{"type":"1","name":"columnsthresholds.color.2.1","value":"FFBF00"},{"type":"1","name":"columnsthresholds.threshold.2.1","value":"80"},{"type":"1","name":"columnsthresholds.color.2.2","value":"FF4000"},{"type":"1","name":"tags.tag.2","value":"region"},{"type":"1","name":"columns.name.3","value":"Disk( \/ )"},{"type":"0","name":"columns.data.3","value":"1"},{"type":"1","name":"columns.item.3","value":"\/: Space utilization"},{"type":"1","name":"columns.timeshift.3","value":""},{"type":"0","name":"columns.aggregate_function.3","value":"0"},{"type":"1","name":"columns.min.3","value":"0"},{"type":"1","name":"columns.max.3","value":"100"},{"type":"0","name":"tags.operator.2","value":"1"},{"type":"0","name":"columns.history.3","value":"1"},{"type":"1","name":"tags.value.2","value":"'$i'"},{"type":"1","name":"columnsthresholds.threshold.3.0","value":"80"},{"type":"1","name":"columns.name.4","value":"Disk( \/u02 )"},{"type":"0","name":"columns.data.4","value":"1"},{"type":"1","name":"columns.item.4","value":"\/u02: Space utilization"},{"type":"1","name":"columns.timeshift.4","value":""},{"type":"0","name":"columns.aggregate_function.4","value":"0"},{"type":"1","name":"columns.min.4","value":"0"},{"type":"1","name":"columns.max.4","value":"100"},{"type":"0","name":"columns.display.4","value":"2"},{"type":"0","name":"columns.history.4","value":"1"},{"type":"1","name":"columns.base_color.4","value":""},{"type":"1","name":"columnsthresholds.color.4.0","value":"FFFF00"},{"type":"1","name":"columnsthresholds.threshold.4.0","value":"80"},{"type":"1","name":"columnsthresholds.color.4.1","value":"FFBF00"},{"type":"1","name":"columnsthresholds.threshold.4.1","value":"90"},{"type":"1","name":"columnsthresholds.color.4.2","value":"FF465C"},{"type":"1","name":"columnsthresholds.threshold.4.2","value":"95"},{"type":"0","name":"columns.data.5","value":"1"},{"type":"1","name":"columns.timeshift.5","value":""},{"type":"0","name":"columns.aggregate_function.5","value":"0"},{"type":"0","name":"columns.display.5","value":"1"},{"type":"0","name":"columns.history.5","value":"1"},{"type":"1","name":"columns.base_color.5","value":""},{"type":"1","name":"columnsthresholds.color.5.0","value":"FF465C"},{"type":"1","name":"columnsthresholds.threshold.5.0","value":"0"},{"type":"0","name":"columns.data.6","value":"1"},{"type":"1","name":"columns.timeshift.6","value":""},{"type":"0","name":"columns.aggregate_function.6","value":"0"},{"type":"0","name":"columns.display.6","value":"1"},{"type":"0","name":"columns.history.6","value":"1"},{"type":"1","name":"columns.base_color.6","value":""},{"type":"1","name":"columnsthresholds.color.7.0","value":"FF465C"},{"type":"1","name":"columnsthresholds.threshold.7.0","value":"0"},{"type":"0","name":"column","value":"1"},{"type":"0","name":"count","value":"100"},{"type":"1","name":"columnsthresholds.color.3.3","value":"E64A19"},{"type":"1","name":"columnsthresholds.threshold.3.3","value":"95"},{"type":"1","name":"columnsthresholds.threshold.2.2","value":"90"},{"type":"0","name":"columns.display.3","value":"2"},{"type":"1","name":"columns.base_color.3","value":"00FF00"},{"type":"1","name":"columnsthresholds.color.3.0","value":"FFEE58"},{"type":"1","name":"columnsthresholds.color.3.1","value":"FFBF00"},{"type":"1","name":"columnsthresholds.threshold.3.1","value":"85"},{"type":"1","name":"columnsthresholds.color.3.2","value":"FF7043"},{"type":"1","name":"columnsthresholds.threshold.3.2","value":"90"},{"type":"1","name":"columnsthresholds.color.7.1","value":"80FF00"},{"type":"1","name":"columnsthresholds.threshold.7.1","value":"1"},{"type":"1","name":"columns.name.7","value":"Agent"},{"type":"0","name":"columns.data.7","value":"1"},{"type":"1","name":"columns.item.7","value":"Zabbix agent availability"},{"type":"1","name":"columns.item.5","value":"Runtime: JVM uptime"},{"type":"1","name":"columns.name.6","value":"Service Status"},{"type":"1","name":"columns.timeshift.7","value":""},{"type":"0","name":"columns.aggregate_function.7","value":"0"},{"type":"0","name":"columns.display.7","value":"1"},{"type":"0","name":"columns.history.7","value":"1"},{"type":"1","name":"columns.base_color.7","value":""},{"type":"1","name":"columns.name.5","value":"JVM Uptime(H:MM)"},{"type":"1","name":"columnsthresholds.color.5.1","value":"BFFF00"},{"type":"1","name":"columnsthresholds.color.6.0","value":"FF465C"},{"type":"1","name":"columnsthresholds.threshold.6.0","value":"0"},{"type":"1","name":"columnsthresholds.color.6.1","value":"00FF00"},{"type":"1","name":"columnsthresholds.threshold.6.1","value":"1"},{"type":"1","name":"tags.tag.1","value":"env"},{"type":"1","name":"tags.value.1","value":"'$ENV'"},{"type":"1","name":"columnsthresholds.color.5.2","value":"BFFF00"},{"type":"1","name":"columnsthresholds.threshold.5.2","value":"1"},{"type":"1","name":"columnsthresholds.threshold.5.1","value":"0.01"},{"type":"1","name":"columns.item.6","value":"Process Check"}]},'
  # Output for debugging
  echo "Placing widget at X:$x Y:$y with Width:$top_widget_width Height:$top_widget_height"

  # Append the widget JSON to the data file
  echo -n "$json_top_hosts_widget" >> $data_file

  # Increment X position for the next widget
  x=$((x + top_widget_width))

  # If X has reached or exceeded the max width, reset X and increment Y for the next row
  if (( x >= dashboard_max_width )); then
    x=0
    y=$((y + top_widget_height))
  fi
done

if (( x + top_widget_width > dashboard_max_width )); then
  x=0
  y=$((y + top_widget_height))
fi

json_problem_widgets='{"type":"problems","name":"","x":"'$x'","y":"'$y'","width":"'$top_widget_width'","height":"'$top_widget_height'","view_mode":"0","fields":[{"type":"1","name":"tags.tag.2","value":"region"},{"type":"0","name":"tags.operator.2","value":"0"},{"type":"1","name":"tags.value.2","value":"'$i'"},{"type":"2","name":"groupids","value":"36"},{"type":"0","name":"severities","value":"3"},{"type":"0","name":"severities","value":"5"},{"type":"1","name":"tags.tag.0","value":"project"},{"type":"0","name":"tags.operator.0","value":"0"},{"type":"1","name":"tags.value.0","value":"'$j'"},{"type":"1","name":"tags.tag.1","value":"env"},{"type":"0","name":"tags.operator.1","value":"0"},{"type":"1","name":"tags.value.1","value":"'$ENV'"}]},'
echo -n "$json_problem_widgets" >> $data_file
x=0
y=$((y + 4))
# Calculate starting position for svggraph widgets
# Ensure y is at the start of the next row if top_hosts widgets didn't exactly fill the last row
if (( y % graph_widget_height != 0 )); then
  y=$(( (y / graph_widget_height + 1) * graph_widget_height ))
fi

# Add svggraph widgets
svggraph_type_list="Threading: Thread Count;Threading: Daemon thread count;Memory: Heap memory maximum size;Memory: Heap memory used;Memory: Non-Heap memory used;Memory: Heap memory committed;Memory: Non-Heap memory committed;Threading: Total started thread count;Threading: Peak thread count;OperatingSystem: File descriptors opened;OperatingSystem: Process CPU Load"
host_group=("eu-we1-c-ejq11.ppe.wpt.local" 
"eu-we1-c-efs11.ppe.wpt.local"  
"eu-we1-c-ggh12.ppe.wpt.local" 
"eu-we1-c-efs22.ppe.wpt.local" 
"eu-we1-c-zrd11.ppe.wpt.local" 
"eu-we1-c-sge11.ppe.wpt.local" 
"eu-we1-c-cnn22.ppe.wpt.local" 
"eu-we1-c-efs13.ppe.wpt.local" 
"eu-we1-c-ggh11.ppe.wpt.local"         
"eu-we1-c-efs-jboss-11.ppe.wpt.local")
IFS=";"
for type in ${svggraph_type_list}; do
  if (( x + graph_widget_width > dashboard_max_width )); then
    x=0
    y=$((y + graph_widget_height))
  fi
  if (( y + graph_widget_height > dashboard_max_height )); then
    echo "Error: Widget placement for 'svggraph' exceeds dashboard height."
    exit 1
  fi

  # Initialize fields array for JSON
  fields_array=""

  for i in "${!host_group[@]}"; do
    host=${host_group[$i]}
    color=$(generate_dark_color)
    fields_array+='{"type":"1","name":"ds.hosts.'$i'.0","value":"'$host'"},{"type":"1","name":"ds.items.'$i'.0","value":"'$type'"},{"type":"1","name":"ds.color.'$i'","value":"'$color'"},'
  done

  # Remove the trailing comma
  fields_array=${fields_array%,}

  json_svggraph_widget='{"type":"svggraph","name":"'$type'","x":'$x',"y":'$y',"width":'$graph_widget_width',"height":'$graph_widget_height',"view_mode":0,"fields":['$fields_array']},'

  echo "Placing widget at X:$x Y:$y with Width:$graph_widget_width Height:$graph_widget_height"
  echo -n "$json_svggraph_widget" >> $data_file
  x=$((x + graph_widget_width))
  # Start a new row after every two widgets
  if (( x >= dashboard_max_width )); then
    x=0
    y=$((y + graph_widget_height))
  fi
done

# Finalize the JSON file
sed -i '$ s/,$//' $data_file  # Remove the last comma
echo -n ']}]},"auth":"'$auth'","id":1}' >> $data_file

# Validate and send the JSON to Zabbix
if ! jq empty $data_file; then
    echo "JSON is invalid. Please check the $data_file file for syntax errors."
    exit 1
fi
curl -k -X POST -H "Content-Type: application/json" --data @$data_file "$zabbix_url"



