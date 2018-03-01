# **groupby**

*groupby* is a simple tool for grouping filenames by their properties.

## Features
* Simple to use: `groupy` will return grouped results in current directory
* Predefined filters or use your own
* Supports similar GNU Parallel notation
* Use filter output for each group in custom commands

## Custom commands
*groupby* supports custom filters and execution of commands on grouped files.
To assist with this, the following syntax is observed:
```buildoutcfg
# filename
{}   -> /foo/bar/file.ogg  -> 
 
# Filename with extension removed
{.}  -> /foo/bar/file

# Basename of file
{/}  -> file.ogg

# Directory of file
{//} -> /foo/bar/

# Basename of file with extension removed
{//} -> file

# File extension
{..} -> .ogg
```
With the exception of {..}, this is a similar syntax to GNU Parallel

### Group Execution
___
When using `-x`/`--exec-group`, an additional expansion is available under the notation of 
`{fn}`, representing the output of that filter for that group.

```buildoutcfg
# Move all files with the same size into their own directory
$ groupby -r -f size -x "mkdir -p {f1}; mv {} {f1}/{/}
 ->  mkdir -p 122254
 ->  mv /foo/bar/file.ogg 122254/file.ogg

# Group all pictures into year and month


```
