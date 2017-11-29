#[macro_use]
extern crate clap;
#[macro_use]
extern crate error_chain;
extern crate pulldown_cmark as pulldown;


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
    let mut file = File::open(Path::new(matches.value_of_os("FILE").unwrap()))
        .chain_err(|| "failed to open markdown file")?;
    let mut buf = String::new();
    file.read_to_string(&mut buf)
        .chain_err(|| "failed to read file contents")?;
    let parser = Parser::new(&buf);
    for event in parser {
        match event {
            Event::Start(tag) => match tag {
                Tag::Link(href, _title) | Tag::Image(href, _title) => {
                    check(href);
                }
                _ => {}
            },
            Event::Html(text) | Event::InlineHtml(text) => {
                let href = text; // FIXME: extract href from html code
                check(href);
            }
            _ => {}
        }
    }
    Ok(())
}
fn check<R>(link: R) -> bool
where
    R: AsRef<str>,
{
    true
}
