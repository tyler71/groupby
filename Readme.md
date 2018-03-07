# **groupby**

*groupby* is a dedicated tool for grouping filenames by their properties.

## Features
* Simple to use: `groupy` will return grouped results in current directory
* Predefined filters or use your own
* Regular Expression filter
* Supports similar GNU Parallel notation
* Use filter output for each group in custom commands
* Ignore or prefer specific directories or files
* Ignores (unless specified)
  * Hidden directories
  * Empty files
  * Symbolic links

## Syntax
```buildoutcfg
usage: groupby.py [-h] [-f FILTERS] [-x GROUP_ACTION] [--include INCLUDE]
                  [--exclude EXCLUDE] [--dir-include DIR_INCLUDE]
                  [--dir-exclude DIR_EXCLUDE] [--dir-hidden] [-r]
                  [-t THRESHOLD] [--basic-formatting] [--max-depth MAX_DEPTH]
                  [--empty-file] [--follow-symbolic] [--interactive] [-v]
                  [directory [directory ...]]

positional arguments:
  directory

optional arguments:
  -h, --help            show this help message and exit
  -f FILTERS, --filters FILTERS
                        Filenames represented as {}: --shell "du {} | cut -f1"
  -x GROUP_ACTION, --exec-group GROUP_ACTION
                        Filenames represented as {}, filters as {f1}, {fn}...:
                        --exec-group "echo {} {f1}"
  --include INCLUDE
  --exclude EXCLUDE
  --dir-include DIR_INCLUDE
  --dir-exclude DIR_EXCLUDE
  --dir-hidden
  -r, --recursive
  -t THRESHOLD, --threshold THRESHOLD
                        Minimum number of files in each group
  --basic-formatting
  --max-depth MAX_DEPTH
  --empty-file          Allow comparision of empty files
  --follow-symbolic     Allow following of symbolic links for compare
  --interactive
  -v, --verbosity
```
## Smart Selection
*groupby* uses the context of the argument to select which method of filter or group command
### Filter
Filters have 3 types
* Builtins
* Shell
* Regular Expression

Builtins include 

## Custom Commands
*groupby* supports execution of commands on grouped files.
To assist with this, brace expansion of the following syntax is observed:
```buildoutcfg
# filename
{}   -> /foo/bar/file.ogg
 
# Filename with extension removed
{.}  -> /foo/bar/file

# Basename of file
{/}  -> file.ogg

# Directory of file
{//} -> /foo/bar

# Basename of file with extension removed
{/.} -> file

# File extension
{..} -> .ogg

# Filter output
{fn} -> output
```
With the exceptions of {..} and {fn}, this brace expansion is a similar syntax to [GNU Parallel](https://www.gnu.org/software/parallel/)

### Group Execution
___
When using `-x`/`--exec-group`, an additional brace expansion is available under the notation of 
`{fn}`, representing the output of that filter for that group.

```buildoutcfg
# Move all files with the same size into their own directory
$ groupby -r -f size -x "mkdir -p {f1}; mv {} {f1}/{/}
# Commands executed
 ->  mkdir -p 122254
 ->  mv /foo/bar/file.ogg 122254/file.ogg

# Group all pictures into year and month
groupby.py -t2 -r \                             
    -s "exiftool -p '\$DateTimeOriginal' {} | cut -d\: -f1" \                   
    -s "exiftool -p '\$DateTimeOriginal' {} | cut -d\: -f2" \                   
    -x "echo mkdir -p {f1}/{f2}; echo mv {} {f1}/{f2}/{/}"  \                   
    foo/bar
# Commands executed
 -> mkdir -p 2015/04
 -> mv foo/bar/image1.png 2015/04/image1.png
...
```
## Filters
*groupby* supports three kinds of filters
* builtin
* shell
* regex

Filters are completed in order, left to right as specified on each file discovered.
### Builtin Filters
*groupby* comes with several builtin filters including
* **md5**:  complete full md5 checksum
* **sha256**: complete full sha256 checksum
* **partial_md5**: md5 checksum of the first 12mb of a file
* **modified**: returns the modified date
* **accessed**: returns the accessed date
* **size**: returns the size in bytes
* **filename**: returns the filename
* **file**: returns the byte data

### Shell Filters
Shell filters, invoked with `-s`/`--shell` require the use of brace expansion to know which file to act on.
For example, ```du -b {}``` will translate to ```du -b foobar.mkv```
Be aware of the output of shell commands. They often include the relative path and filename
in the output. *Output should be sanitized to only include the output of the command* through
tools such as cut or grep. For example
```buildoutcfg
du -b {} -> du -b foobar.mkv -> 476027 foobar.mkv
du -b {} -> du -b foobar.mkv | cut -f1 -> 476027
grep -oE '[0-9]+' {} -> grep -oE '[0-9]+' foobar.mkv -> 476027
```
See Custom Commands for more information on brace expansion

### Regular Expression Filters (regex)
[Python based regular expressions](https://docs.python.org/3/library/re.html) 
may be invoked with `--regex`

Filenames often carry unique information about a file, such as
* resolution for videos
* bit-rate for audio
* versions of software

This information can be used to group the files.

```buildoutcfg
# foo/foo2_1080p.mkv
# foo/bar_720p.mkv
# foo/foo4_720p.mkv
# foo/foo6_480p.mkv

groupby --regex '\d{3,4}p' foo/
# '\d{3,4}p' == Match 3 or 4 digits and then a character of 'p'
# Output
-> foo/foo6_480p.mkv
->
-> foo/foo4_720p.mkv
->     foo/bar_720p.mkv
->
-> foo/foo2_1080p.mkv
```
The regex match may also be used as notation for custom shell commmands

```buildoutcfg
groupby --regex '\d+p' foo -x "mkdir -p {f1}/{/}"
# Commands executed
-> mkdir -p 480p/foo6_480p.mkv
-> mkdir -p 720p/foo4_720p.mkv
-> mkdir -p 720p/bar_720p.mkv
-> mkdir -p 1080p/foo2_1080p.mkv
```
