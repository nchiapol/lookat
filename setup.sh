# simple script to prepare lookat for usage
#   - creates an alias to lookat
#   - adds the directory containing this script to PYTHONPATH

location=`dirname $BASH_SOURCE`
cd $location
here=`pwd`
cd - > /dev/null
echo "adding $here to PYTHONPATH"
export PYTHONPATH="$here:$PYTHONPATH"
echo "creating alias for lookat"
alias lookat="$here/lookat/__init__.py"

