#!/usr/bin/env bash

file_m3u8=$1

declare -a playlists=($(cat $file_m3u8 | grep -E "(http|https)://*"))

download_ts() {
    url=$1
    output_path=$2
    file_name=$3

    until https --quiet --download $url --output $output_path/$file_name; do
        sleep 5
    done
}


function show_progress {
    current="$1"
    total="$2"

    bar_size=40
    bar_char_done="#"
    bar_char_todo="-"
    bar_percentage_scale=2

    # calculate the progress in percentage
    percent=$(bc <<< "scale=$bar_percentage_scale; 100 * $current / $total" )
    # The number of done and todo characters
    done=$(bc <<< "scale=0; $bar_size * $percent / 100" )
    todo=$(bc <<< "scale=0; $bar_size - $done" )

    # build the done and todo sub-bars
    done_sub_bar=$(printf "%${done}s" | tr " " "${bar_char_done}")
    todo_sub_bar=$(printf "%${todo}s" | tr " " "${bar_char_todo}")

    # output the bar
    echo -ne "\rProgress ${current}/${total} : [${done_sub_bar}${todo_sub_bar}] ${percent}%"

    if [ $total -eq $current ]; then
        echo -e "\nDONE"
    fi
}

mkdir -p ts
rm -rf merge.txt
touch merge.txt

for i in ${!playlists[@]}; do
    if [ ! -f ts/${i}.ts ]; then
        download_ts "${playlists[$i]}" "ts" "${i}_png.ts"
        xxd -ps -c 0 ts/${i}_png.ts | sed -E "s/^[A-Za-z0-9].*44ae4260//" | xxd -ps -r > ts/${i}.ts
        rm -rf ts/${i}_png.ts
    fi
    echo "file ts/${i}.ts" >> merge.txt
    show_progress $(($i+1)) ${#playlists[@]}
done
