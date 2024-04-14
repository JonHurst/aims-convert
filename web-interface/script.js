"use strict";

const AIMS_URL = "https://kvq58p5uqk.execute-api.eu-west-2.amazonaws.com/default/aims-roster-data-extraction";

let ID = x => document.getElementById(x);


function get_format() {
    for(const format of ["efj", "ical", "csv"]) {
        if(ID(format).checked)
            return format;
    }
}


function get_options() {
    let options = [];
    for(const option of ["ade"]) {
        if(ID(option).checked)
            options.push(option);
    }
    return options;
}


let format_handlers = Object();
format_handlers["efj"] = () => {
    ID("ical_options").classList.add("hidden");
};
format_handlers["ical"] = () => {
    ID("ical_options").classList.remove("hidden");
};
format_handlers["csv"] = () => {
    ID("ical_options").classList.add("hidden");
}


function dragoverHandler(ev) {
    ev.preventDefault();
    ev.dataTransfer.dropEffect = "copy";
}


function dropHandler(ev) {
    ev.preventDefault();
    if (!ev.dataTransfer.items) return;
    for(const item of ev.dataTransfer.items) {
        if (item.kind === "file") {
            const file = item.getAsFile();
            process_file(file);
            break;
        }
    }
}


async function process_file(file) {
    const output = ID("output");
    if (file) {
        output.value = "Working…";
        let roster = await file.text();
        let response = await fetch(AIMS_URL, {
            method: "POST",
            body: JSON.stringify({
                "roster": roster,
                "format": get_format(),
                "options": get_options(),
            }),
            cache: "no-cache"
        });
        let result = await response.json();
        output.value = result;
    }
}


async function save_output_to_file() {
    const data = ID("output").value;
    const file = new window.Blob([data], {type: "text/plain"});
    const a = document.createElement("a");
    const url = window.URL.createObjectURL(file);
    a.href = url;
    const filenames = {"efj": "journal.txt",
                       "csv": "roster.csv",
                       "ical": "roster.ics"};
    a.download = filenames[get_format()];
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}


async function copy_output_to_clipboard() {
    let cb = window.navigator.clipboard;
    console.log(cb);
    await cb.writeText(ID("output").value);
    window.alert("Copied to clipboard");
}


function main() {
    for(const el of ["efj", "ical", "csv"]) {
        document.getElementById(el).addEventListener(
            "click",
            () => {
                ID("output").value = "";
                format_handlers[el]();
            }
        );
    }
    const input = ID("input");
    input.addEventListener(
        "change",
        async () => { if(input.files.length == 1) process_file(input.files[0]);});
    input.addEventListener(
        "click",
        function () {this.value = null;});
    ID("load_roster").addEventListener(
        "click",
        () => {ID("output").value = ""; input.click();});
    ID("save").addEventListener("click", save_output_to_file);
    ID("copy").addEventListener("click", copy_output_to_clipboard);
    ID("help").addEventListener("click", () => window.open(
        "https://hursts.org.uk/aimsdocs/webapp.html", "_blank"));
    ID("efj").click();
}

window.addEventListener("load", main);
