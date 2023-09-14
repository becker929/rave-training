# clean up & create .aws directory
rm -rf ~/.aws
mkdir ~/.aws

# create credentials file
touch  ~/.aws/credentials
lines_to_add=(
'[default]'
"aws_access_key_id = $1"
"aws_secret_access_key = $2"
)

for line in "${lines_to_add[@]}"; do
    grep -Fxq "$line" ~/.aws/credentials || echo "$line" >> ~/.aws/credentials
done

# create config file
touch ~/.aws/config
lines_to_add=(
'[default]'
'region = us-west-2'
)
for line in "${lines_to_add[@]}"; do
    grep -Fxq "$line" ~/.aws/config || echo "$line" >> ~/.aws/config
done
