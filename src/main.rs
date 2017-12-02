#[macro_use]
extern crate clap;
#[macro_use]
extern crate error_chain;
extern crate pulldown_cmark as pulldown;
extern crate reqwest;

use clap::{App, Arg};
use std::path::Path;
use std::fs::File;
use pulldown::{Event, Parser, Tag};
use std::io::Read;

mod error {
    error_chain!{}
}

use error::*;

quick_main!(run);

fn run() -> Result<()> {
    let client = reqwest::Client::new();
    let matches = App::new(crate_name!())
        .version(crate_version!())
        .author(crate_authors!())
        .about(crate_description!())
        .arg(
            Arg::with_name("FILE")
                .help("Sets the markdown file to check the links in.")
                .required(true),
        )
        .get_matches();
    let contents = {
        let mut file = File::open(Path::new(matches.value_of_os("FILE").unwrap()))
            .chain_err(|| "failed to open markdown file")?;
        let mut buf = String::new();
        file.read_to_string(&mut buf)
            .chain_err(|| "failed to read file contents")?;
        buf
    };
    let parser = Parser::new(&contents);
    for event in parser {
        match event {
            Event::Start(tag) => match tag {
                Tag::Link(href, _title) | Tag::Image(href, _title) => {
                    match client.get(href.as_ref()).send() {
                        Ok(response) => {
                            println!("{}: {}", href, response.status());
                        }
                        Err(e) => {
                            println!("{}: ERROR {:?}", href, e);
                        }
                    }
                }
                _ => {}
            },
            Event::Html(text) | Event::InlineHtml(text) => {
                let _ = text;
                // FIXME: extract href from html code
            }
            _ => {}
        }
    }
    Ok(())
}
