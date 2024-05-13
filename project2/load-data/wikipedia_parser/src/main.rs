use std::fs::File;
use std::io::Write;

use json_writer::{JSONWriter, PrettyJSONWriter};
use quick_xml::events::Event;
use quick_xml::reader::Reader;

#[derive(Debug, PartialEq)]
enum TagType {
    Title,
    Text,
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let file_path = "../articles/decompressed/enwiki-20240401-pages-articles1.xml-p1p41242";

    let mut reader = Reader::from_file(file_path).unwrap();
    reader.trim_text(true);
    let mut buffer = Vec::new();

    // let cur_title = None;
    let mut cur_tag: Option<TagType> = None;

    let mut file_writer = File::create("out.json")?;
    let mut json_buffer = String::new();
    let mut json_writer = PrettyJSONWriter::new(&mut json_buffer);

    let mut title = String::new();

    println!("Parsing file: {file_path}");
    let start = std::time::Instant::now();

    let mut first = true;
    json_writer.json_begin_array();
    loop {
        match reader.read_event_into(&mut buffer)? {
            Event::Start(e) if e.name().as_ref() == b"title" => cur_tag = Some(TagType::Title),
            Event::End(e) if e.name().as_ref() == b"title" => cur_tag = None,
            Event::Start(e) if e.name().as_ref() == b"text" => cur_tag = Some(TagType::Text),
            Event::End(e) if e.name().as_ref() == b"text" => cur_tag = None,
            Event::Text(e) => {
                if cur_tag == Some(TagType::Title) {
                    let content = e.unescape()?;
                    title = content.into_owned();
                } else if cur_tag == Some(TagType::Text) {
                    let content = e.unescape()?;

                    json_writer.json_begin_array_value(first);
                    first = false;
                    json_writer.json_begin_object();
                    json_writer.json_object_key("title", true);
                    json_writer.json_string(&title);
                    json_writer.json_object_key("body", false);
                    json_writer.json_string(&content);
                    json_writer.json_end_object(false);
                }
            }
            Event::Eof => {
                break;
            }
            _ => {}
        }
    }
    json_buffer.json_end_array(false);

    let end = std::time::Instant::now();
    println!("Parsed file in {:.2}s", (end - start).as_secs_f32());

    file_writer.write_all(json_buffer.as_bytes())?;

    Ok(())
}
