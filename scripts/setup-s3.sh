# get credentials from arguments
YOUR_ACCESS_KEY_ID = $1
YOUR_SECRET_ACCESS_KEY = $2

touch  ~/.aws/credentials
lines_to_add=(
'[default]'
"aws_access_key_id = ${YOUR_ACCESS_KEY_ID}"
"aws_secret_access_key = ${YOUR_SECRET_ACCESS_KEY}"
)

for line in "${lines_to_add[@]}"; do
    grep -Fxq "$line" ~/.aws/credentials || echo "$line" >> ~/.aws/credentials
done

touch ~/.aws/config
lines_to_add=(
'[default]'
'region = us-west-2'
)

for line in "${lines_to_add[@]}"; do
    grep -Fxq "$line" ~/.aws/config || echo "$line" >> ~/.aws/config
done
