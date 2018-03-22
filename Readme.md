# **groupby**

*groupby* is a tool for grouping files by their properties.

## Features
* Simple to use: `groupy` will return grouped results in current directory
* Builtin or shell filters
* Supports similar GNU Parallel notation
* Execute commands on each grouped file
* Ignore or prefer specific directories or files
* Safe with invalid encoding or maliciously named filenames
* Ignores (unless specified)
  * Hidden directories
  * Empty files
  * Symbolic links

## Syntax
```commandline
usage: groupby [-h] [-f FILTER] [-x COMMAND] [-m DIRECTORY] [--exec-remove]
               [--exec-link] [--exec-basic-formatting] [-r] [--include FILE]
               [--exclude FILE] [--dir-include DIRECTORY]
               [--dir-exclude DIRECTORY] [--dir-hidden] [--max-depth DEPTH]
               [--empty-file] [--follow-symbolic] [-g SIZE] [-v]
               [directory [directory ...]]

positional arguments:
  directory

optional arguments:
  -h, --help            show this help message and exit
  -f FILTER, --filter FILTER
                        builtin filters
                        modifiers with syntax filter:modifier
                          partial_md5
                          md5
                          sha     :[1, 224, 256, 384, 512, 3_224, 3_256, 3_384, 3_512]
                          modified:[MICROSECOND, SECOND, MINUTE, HOUR, DAY, MONTH, YEAR, WEEKDAY]
                          accessed:[MICROSECOND, SECOND, MINUTE, HOUR, DAY, MONTH, YEAR, WEEKDAY]
                          size    :[B, KB, MB, GB, TB, PB]
                          filename:'EXPRESSION'
                          file
                        example: -f modified
                                 -f size:mb
                        
                        shell filters
                        filenames represented as {}: 
                        example: -f "du {} | cut -f1"
                                 -f "exiftool -p '\$DateTimeOriginal' {} | cut -d\: -f1"
  -x COMMAND, --exec-shell COMMAND
                        complete shell command on grouped files
                        notation:
                          {}  : path and filename
                          {.} : filename, extension removed
                          {/} : filename, path removed
                          {//}: path of filename
                          {/.}: filename, extension and path removed
                          {..}: extension of filename
                          {fn}: filter output of filter n
                        example: -x "mkdir {f1}; mv {} {f1}/{/}"
                                 -x "mkdir {f1}; ffmpeg -i {} ogg/{/.}.ogg"
  -m DIRECTORY, --exec-merge DIRECTORY
                        syntax DIRECTORY:MODIFIER
                        default = DIRECTORY:COUNT
                        COUNT : increment conflicting filenames
                                foo.mkv -> foo_0001.mkv
                        IGNORE: skip conflicting filenames
                        ERROR : exit the program if conflicting filename found
                        
                        replace conflicting filenames with CONDITION
                        LARGER
                        SMALLER
                        NEWER
                        OLDER
                        example: -m foo:LARGER
                                 -m foo:ERROR
  --exec-remove
  --exec-link
  --exec-basic-formatting
                        no indenting or empty newlines in standard output
  -r, --recursive
  --include FILE
  --exclude FILE
  --dir-include DIRECTORY
  --dir-exclude DIRECTORY
  --dir-hidden
  --max-depth DEPTH
  --empty-file          Allow comparision of empty files
  --follow-symbolic     allow following of symbolic links for compare
  -g SIZE, --group-size SIZE
                        Minimum number of files in each group
  -v, --verbosity
```

## Brace Expansion
*groupby* supports execution of commands on grouped files.
To assist with this, brace expansion of the following syntax is observed:
```commandline
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
With the exceptions of `{..}` and `{fn}`, this brace expansion is a similar syntax to [GNU Parallel's Context Replace](https://www.gnu.org/software/parallel/man.html#EXAMPLE:-Context-replace)

Filenames with invalid encoding or with characters with special meaning to the shell are quoted.
```commandline
groupby -x "echo {}"
-> echo '/path/foobar.ogg; malicous_command'
 /path/foobar.ogg; malicous_command
groupby -x "echo {/}"
-> echo 'foobar.ogg; malicous_command'
 foobar.ogg; malicous_command
```
Invalid encoding is also sanitized before printing to the screen, however actions can be completed on it

For example, a file with invalid encoding will be replaced with `?`  `R??ڀ?2??z?&?̀?????B?A?I?P?CvJ??` prior to printing on the screen
but file actions will be done on the original filename

## Filters
*groupby* supports two kinds of filters
* builtin
* shell

Filters are completed in order, left to right as specified on each file discovered.
### Builtin Filters
*groupby* comes with several builtin filters including
* **md5**:  complete full md5 checksum
* **sha**: complete full sha checksum
* **partial_md5**: md5 checksum of the first 12mb of a file
* **modified**: returns the modified date
* **accessed**: returns the accessed date
* **size**: returns the size in bytes
* **filename**: returns the filename
* **file**: returns the byte data

#### Customizing Builtin
Additionally, these filters allow modifiers of the output
```commandline
sha     :[1, 224, 256, 384, 512, 3_224, 3_256, 3_384, 3_512]
modified:[MICROSECOND, SECOND, MINUTE, HOUR, DAY, MONTH, YEAR, WEEKDAY]
accessed:[MICROSECOND, SECOND, MINUTE, HOUR, DAY, MONTH, YEAR, WEEKDAY]
size    :[B, KB, MB, GB, TB, PB]
filename:'EXPRESSION'
```

The syntax follows a common format of `filter:OPTION`, delimited by a '`:`'

If omitted, uses the default or unmodified output
##### SHA
SHA permits multiple checksum levels to group by.

Syntax: 
```commandline
-f sha:[1, 224, 256, 384, 512, 3_224, 3_256, 3_384, 3_512]
```

For example, `-f sha:256` will invoke a sha256 checksum on the file

##### DATETIME
`modified` and `accessed` permit rounding of their reported times.

Syntax: 
```commandline
-f modified:[MICROSECOND, SECOND, MINUTE, HOUR, DAY, MONTH, YEAR, WEEKDAY]
-f accessed:[MICROSECOND, SECOND, MINUTE, HOUR, DAY, MONTH, YEAR, WEEKDAY]
```

For example, `-f modified:HOUR` will group files that have been modified in the same hour

Abbreviations:
* MICROSECOND: `NANO` `MICRO` `MICROSECONDS`
* SECOND: `S` `SEC` `SECONDS`
* MINUTE: `M` `MIN` `MINUTES`
* HOUR: `H` `HOURS`
* DAY: `D` `DAYS`
* MONTH: `MON` `MONTHS`
* YEAR: `Y` `YR` `YEARS`
* WEEKDAY: `WD` `WEEKDAYS`

##### FILENAME
[Python based regular expressions](https://docs.python.org/3/library/re.html) are permitted on filenames

Syntax: 
```commandline
-f filename:'EXPRESSION'
```

Filenames often carry unique information about a file, such as
* resolution for videos
* bit-rate for audio
* versions of software

This information can be used to group the files.

```commandline
# foo/foo2_1080p.mkv
# foo/bar_720p.mkv
# foo/foo4_720p.mkv
# foo/foo6_480p.mkv

$ groupby -f filename:'\d{3,4}p' foo/
# '\d{3,4}p' == Match 3 or 4 digits and then a character of 'p'
# Output
-> foo/foo6_480p.mkv
->
-> foo/foo4_720p.mkv
->     foo/bar_720p.mkv
->
-> foo/foo2_1080p.mkv
```
If capture groups are part of the expression, only the captured groups are returned

Below, the string must have a `.` followed by 2-4 alphanumeric characters and end the string,
but it will only return a result of the 2-4 alphanumeric characters

```commandline
$ groupby -f filename:'\.(\w{2,4})$'
# Output
-> mkv
-> mkv
-> mkv
-> mkv
```
Sometimes it is useful to use groups as part of a expression without wanting to turn up in the output.

In these cases, use non capturing groups `(?:)`
```commandline
$ groupby -v -f filename:'(document)_\d?(?:\.\w+){1,2}' foo
[INFO] document
foo/document_1.tar
    foo/document_2.tar.gz
    foo/document_1.tar.gz
```
The output of this expression is available with the notation {fn} like other filters

```commandline
groupby -f filename:'\d+p' foo -x "mkdir -p {f1}/{/}"
# Commands executed
-> mkdir -p 480p/foo6_480p.mkv
-> mkdir -p 720p/foo4_720p.mkv
-> mkdir -p 720p/bar_720p.mkv
-> mkdir -p 1080p/foo2_1080p.mkv
```

##### SIZE
Size permit rounding of reported byte size

Syntax:
```commandline
-f size:[B, KB, MB, GB, TB, PB]
```

For example, `-f size:MB` will output filenames rounded by the nearest megabyte

Abbrevations:
* BYTE: `B` `BYTES`
* KILOBYTE: `KB` `KILO` `KILOBYTES`
* MEGABYTE: `MB` `MEGA` `MEGABYTES`
* GIGABYTE: `GB` `GIGA` `GIGABYTES`
* TERABYTE: `TB` `TERA` `TERABYTES`
* PETABYTE: `PB` `PETA` `PETABYTES`


### Shell Filters
Shell filters, invoked similary with `-f`/`--filter` require the use of brace expansion to know which
file to act on and to identify it as a shell filter.

For example, ```du -b {}``` will translate to ```du -b foobar.mkv```

Be aware of the output of shell commands. They often include the relative path and filename
in the output. *Output should be sanitized to only include the relative output of the command* through
tools such as `cut` or `grep`. For example
```commandline
du -b {} 
    -> 476027 foobar.mkv              # Bad
du -b {} | cut -f1 
    -> 476027                         # Better
du -b {} | grep -oE '^[0-9]+'
    -> 476027                         # Better
```
## Group Execution
The results are grouped by their filters and can be acted on.
Only the last action specified will be used.
There are 2 types of group execution
* **builtin**: Executes the builtin on the grouped files
* **shell**: Executes the shell command on each grouped file

### Builtin
*groupby* has 3 built in actions on grouped files
* **Link**: for each group, hardlink the first file to all the others in the group
* **Remove**: for each group, remove all but the first file
* **Merge**: Merge directories into the merge directory

#### Link
For each group, the first file is used as the source. The other files in the group
are removed. Then a hard link from source -> removed files location occurs.
This is useful for minimzing disk space usage when the files are the same, and won't
be changed. For example, with RAW image formats where the editing is completed by a configuration file

#### Remove
For each group, the first file is kept while additional files are removed.

#### Merge
Take all directories and merge into the given directory. For example,

`groupby --exec-merge testdir foo1 foo2`
will merge *foo1* and *foo2* into *testdir*.

The testdir structure is generated by filter output.
For example:

```commandline
$ groupby -f size -v
# Output
INFO] 5
foo1.mp4
[INFO] 3
foo2.mp4
[INFO] 10
foo3.mp4

$ groupby -f size -m testdir
# Output
testdir/5/foo1.mp4
testdir/3/foo2.mp4
testdir/10/foo3.mp4
```

Merge also has 7 different methods for handling existing file conflicts.
If unspecified, defaults to COUNT
* COUNT
* IGNORE
* ERROR
* NEWER
* OLDER
* LARGER
* SMALLER

##### Count
Syntax: `--exec-merge testdir:COUNT`

Add a increment count. `foo.mp4` -> `foo_0001.mp4`
##### Ignore
Syntax: `--exec-merge testdir:IGNORE`

Ignore existing files
##### Error
Syntax: `--exec-merge testdir:ERROR`

Raise a error and kill the program

##### CONDITION
There are 4 conditional types of conflicting filename handling
* NEWER
* OLDER
* LARGER
* SMALLER

Each test is completed with the target file compared against the already copied file.
The result is only the CONDITION of files are copied over.
For example,
```
groupby -f size --exec-merge testdir:SMALLER
```
Will result in only the smaller of conflicting files to exist
### Shell
When using `-x`/`--exec-shell`, an additional brace expansion is available under the notation of 
`{fn}`, representing the output of that filter for that group.

```commandline
# Move all files with the same size into their own directory
$ groupby -r -f size -x "mkdir -p {f1}; mv {} {f1}/{/}
# Commands executed
 ->  mkdir -p 122254
 ->  mv /foo/bar/file.ogg 122254/file.ogg

# Group all pictures into year and month
groupby.py -g2 -r \                             
    -f "exiftool -p '\$DateTimeOriginal' {} | cut -d\: -f1" \                   
    -f "exiftool -p '\$DateTimeOriginal' {} | cut -d\: -f2" \                   
    -x "echo mkdir -p {f1}/{f2}; echo mv {} {f1}/{f2}/{/}"  \                   
    foo/bar
# Commands executed
 -> mkdir -p 2015/04
 -> mv foo/bar/image1.png 2015/04/image1.png
...
```

