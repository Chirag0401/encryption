# ... [earlier part of the script remains unchanged]

for j in $( echo $project)
do
for i in $(echo $REGION)
do
if [[ $j == "wpt" ]]; then
for netgroup in CORE DMZ
do
# ... [previous code in the loop]

json_part2='{"type":"tophosts","name":"'$ENV'-'$j'-'$i'-'$netgroup'","x":"'$placex'","y":"'$placey'","width":"11","height":"8","view_mode":"0","fields":[...existing fields...,{"type":"1","name":"columns.name.6","value":"Service Uptime(H:MM)"},{"type":"0","name":"columns.data.6","value":"1"},{"type":"1","name":"columns.item.6","value":"Runtime: JVM uptime"},{"type":"1","name":"columns.timeshift.6","value":""},{"type":"0","name":"columns.aggregate_function.6","value":"0"},{"type":"0","name":"columns.display.6","value":"1"},{"type":"0","name":"columns.history.6","value":"1"},{"type":"1","name":"columns.base_color.6","value":""},{"type":"1","name":"columnsthresholds.color.6.0","value":"FF465C"},{"type":"1","name":"columnsthresholds.threshold.6.0","value":"0"},{"type":"1","name":"columnsthresholds.color.6.1","value":"80FF00"},{"type":"1","name":"columnsthresholds.threshold.6.1","value":"0.01"},{"type":"1","name":"columnsthresholds.color.6.2","value":"BFFF00"},{"type":"1","name":"columnsthresholds.threshold.6.2","value":"1"}]}'

# ... [rest of the loop code]

done
else

# ... [else part code]

json_part2='{"type":"tophosts","name":"'$ENV'-'$j'-'$i'","x":"'$placex'","y":"'$placey'","width":"11","height":"8","view_mode":"0","fields":[...existing fields...,{"type":"1","name":"columns.name.6","value":"Service Uptime(H:MM)"},{"type":"0","name":"columns.data.6","value":"1"},{"type":"1","name":"columns.item.6","value":"Runtime: JVM uptime"},{"type":"1","name":"columns.timeshift.6","value":""},{"type":"0","name":"columns.aggregate_function.6","value":"0"},{"type":"0","name":"columns.display.6","value":"1"},{"type":"0","name":"columns.history.6","value":"1"},{"type":"1","name":"columns.base_color.6","value":""},{"type":"1","name":"columnsthresholds.color.6.0","value":"FF465C"},{"type":"1","name":"columnsthresholds.threshold.6.0","value":"0"},{"type":"1","name":"columnsthresholds.color.6.1","value":"80FF00"},{"type":"1","name":"columnsthresholds.threshold.6.1","value":"0.01"},{"type":"1","name":"columnsthresholds.color.6.2","value":"BFFF00"},{"type":"1","name":"columnsthresholds.threshold.6.2","value":"1"}]}'

# ... [rest of the else part code]

fi
done
done

# ... [rest of the script]
