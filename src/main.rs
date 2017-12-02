extern crate failure;
extern crate pulldown_cmark as pulldown;
extern crate reqwest;
extern crate structopt;
#[macro_use]
extern crate structopt_derive;

use std::fs::File;
use pulldown::{Event, Parser, Tag};
use std::io::Read;
use failure::{Error, ResultExt};
use structopt::StructOpt;

#[derive(StructOpt, Debug)]
struct Args {
    #[structopt(help = "Markdown file to check.")] file: String,
}
type Result<T> = ::std::result::Result<T, Error>;

fn main() {
    if let Err(e) = run(Args::from_args()) {
        eprintln!("error: {}", e.backtrace());
    }
}

fn run(args: Args) -> Result<()> {
    let client = reqwest::Client::new();
    let contents = {
        let mut buf = String::new();
        { File::open(args.file).context("failed to open markdown file")? }
            .read_to_string(&mut buf)
            .context("failed to read file contents")?;
        buf
    };
    let parser = Parser::new(&contents);
    for event in parser {
        let url = match event {
            Event::Start(tag) => match tag {
                Tag::Link(href, _title) | Tag::Image(href, _title) => href,
                _ => continue,
            },
            // FIXME: extract urls from html code
            Event::Html(_html) | Event::InlineHtml(_html) => continue,
            _ => continue,
        };
        match client.get(url.as_ref()).send() {
            Ok(response) => {
                println!("{}: {}", url, response.status());
            }
            Err(e) => {
                println!("{}: ERROR {:?}", url, e);
            }
        }
    }
    Ok(())
}
